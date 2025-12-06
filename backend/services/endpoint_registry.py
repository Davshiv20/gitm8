from functools import wraps
from typing import Callable, Dict, Any, Optional, List
from enum import Enum
import inspect
from typing import get_type_hints
from fastapi import FastAPI, HTTPException, Body, Query, Path, APIRouter
from pydantic import create_model
import logging

logger = logging.getLogger(__name__)

class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"

class EndpointRegistry:
    """Registry to store all registered endpoints"""
    def __init__(self):
        self.endpoints: Dict[str, Dict[str, Any]] = {}
    
    def register(
        self, 
        name: str, 
        func: Callable, 
        method: HTTPMethod, 
        path: Optional[str] = None,
        tags: Optional[List[str]] = None,
        service_class: Optional[Any] = None
    ):
        """Register a function as an endpoint"""
        # Get type hints, handling both regular functions and methods
        try:
            type_hints = get_type_hints(func)
        except Exception:
            type_hints = {}
        
        # Check if it's a method (has 'self' parameter)
        sig = inspect.signature(func)
        is_method = any(p.name == 'self' for p in sig.parameters.values())
        
        self.endpoints[name] = {
            "func": func,
            "method": method,
            "path": path or f"/{name.replace('_', '-')}",
            "signature": sig,
            "type_hints": type_hints,
            "tags": tags or [],
            "service_class": service_class,  # Store class name or class itself
            "is_async": inspect.iscoroutinefunction(func),
            "is_method": is_method
        }
        logger.info(f"Registered endpoint: {method.value} {self.endpoints[name]['path']} ({name})")
    
    def get_all(self):
        """Get all registered endpoints"""
        return self.endpoints


# Global registry instance
registry = EndpointRegistry()


def generate_routes(prefix: str = "/api", service_instances: Optional[Dict[str, Any]] = None) -> APIRouter:
    """
    Generate FastAPI routes from all registered endpoints
    
    Args:
        prefix: URL prefix for all generated routes (default: "/api")
        service_instances: Dictionary mapping service class names to instances
    
    Returns:
        APIRouter: Router with all generated routes
    """
    router = APIRouter()
    service_instances = service_instances or {}
    
    for name, endpoint_info in registry.get_all().items():
        try:
            func = endpoint_info["func"]
            method = endpoint_info["method"]
            path = endpoint_info["path"]
            sig = endpoint_info["signature"]
            type_hints = endpoint_info["type_hints"]
            tags = endpoint_info["tags"]
            service_class = endpoint_info["service_class"]
            is_async = endpoint_info["is_async"]
            is_method = endpoint_info["is_method"]
            
            # Get service instance if this is a method
            service_instance = None
            if is_method and service_class:
                # service_class might be a string name or the class itself
                if isinstance(service_class, str):
                    service_instance = service_instances.get(service_class)
                else:
                    class_name = service_class.__name__
                    service_instance = service_instances.get(class_name)
            
            # Skip 'self' parameter for class methods
            params = {k: v for k, v in sig.parameters.items() if k != 'self'}
            
            # Create route handler with proper closure
            if method in [HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.PATCH]:
                # For POST/PUT/PATCH, create a request body model
                fields = {}
                for param_name, param in params.items():
                    param_type = type_hints.get(param_name, Any)
                    if param.default != inspect.Parameter.empty:
                        fields[param_name] = (param_type, param.default)
                    else:
                        fields[param_name] = (param_type, ...)
                
                # Create dynamic Pydantic model
                RequestModel = create_model(f"{name}_Request", **fields)
                
                # Create route handler with proper closure
                def make_handler(f=func, si=service_instance, async_func=is_async, is_meth=is_method):
                    if async_func:
                        async def route_handler(request: RequestModel = Body(...)):
                            try:
                                if is_meth and si:
                                    result = await f(si, **request.model_dump())
                                else:
                                    result = await f(**request.model_dump())
                                return result
                            except HTTPException:
                                raise
                            except Exception as e:
                                logger.error(f"Error in endpoint {name}: {e}", exc_info=True)
                                raise HTTPException(status_code=500, detail=str(e))
                    else:
                        async def route_handler(request: RequestModel = Body(...)):
                            try:
                                if is_meth and si:
                                    result = f(si, **request.model_dump())
                                else:
                                    result = f(**request.model_dump())
                                return result
                            except HTTPException:
                                raise
                            except Exception as e:
                                logger.error(f"Error in endpoint {name}: {e}", exc_info=True)
                                raise HTTPException(status_code=500, detail=str(e))
                    return route_handler
                
                route_handler = make_handler()
                route_handler.__name__ = func.__name__
                route_handler.__doc__ = func.__doc__ or f"{name} endpoint"
                
            else:  # GET, DELETE
                # For GET/DELETE, use query/path parameters
                def make_handler(f=func, si=service_instance, async_func=is_async, sig_params=params, is_meth=is_method):
                    # Build function signature with Query/Path annotations
                    new_params = []
                    for param_name, param in sig_params.items():
                        param_type = type_hints.get(param_name, Any)
                        # Check if param is in path (simple heuristic: if path contains {param_name})
                        if f"{{{param_name}}}" in path or f"{{username}}" in path.lower():
                            annotation = Path(...) if param.default == inspect.Parameter.empty else Path(default=param.default)
                        else:
                            annotation = Query(...) if param.default == inspect.Parameter.empty else Query(default=param.default)
                        new_params.append(inspect.Parameter(
                            param_name,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            default=param.default if param.default != inspect.Parameter.empty else annotation,
                            annotation=param_type
                        ))
                    
                    new_sig = inspect.Signature(new_params)
                    
                    if async_func:
                        async def route_handler(**kwargs):
                            try:
                                # Extract actual values from Query/Path objects
                                clean_kwargs = {}
                                for k, v in kwargs.items():
                                    if hasattr(v, '__dict__'):
                                        # It's a Query/Path object, extract the default
                                        clean_kwargs[k] = getattr(v, 'default', v)
                                    else:
                                        clean_kwargs[k] = v
                                
                                if is_meth and si:
                                    result = await f(si, **clean_kwargs)
                                else:
                                    result = await f(**clean_kwargs)
                                return result
                            except HTTPException:
                                raise
                            except Exception as e:
                                logger.error(f"Error in endpoint {name}: {e}", exc_info=True)
                                raise HTTPException(status_code=500, detail=str(e))
                    else:
                        async def route_handler(**kwargs):
                            try:
                                clean_kwargs = {}
                                for k, v in kwargs.items():
                                    if hasattr(v, '__dict__'):
                                        clean_kwargs[k] = getattr(v, 'default', v)
                                    else:
                                        clean_kwargs[k] = v
                                
                                if is_meth and si:
                                    result = f(si, **clean_kwargs)
                                else:
                                    result = f(**clean_kwargs)
                                return result
                            except HTTPException:
                                raise
                            except Exception as e:
                                logger.error(f"Error in endpoint {name}: {e}", exc_info=True)
                                raise HTTPException(status_code=500, detail=str(e))
                    
                    route_handler.__signature__ = new_sig
                    return route_handler
                
                route_handler = make_handler()
                route_handler.__name__ = func.__name__
                route_handler.__doc__ = func.__doc__ or f"{name} endpoint"
            
            # Register with router
            router_method = getattr(router, method.value.lower())
            router_method(
                path,
                name=name,
                tags=tags,
                summary=func.__doc__ or f"{name} endpoint"
            )(route_handler)
            
            logger.info(f"Generated route: {method.value} {prefix}{path}")
            
        except Exception as e:
            logger.error(f"Failed to generate route for {name}: {e}", exc_info=True)
    
    logger.info(f"✅ Generated {len(registry.get_all())} routes with prefix {prefix}")
    return router
    