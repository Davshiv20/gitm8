from fastapi import FastAPI, APIRouter, HTTPException
from models import UserCompatibilityRequest 
from services.analytics_service import analyze_compatibility_metrics, get_complete_user_info, create_radar_chart_data
from services.llm_service import call_llm_api, create_llm_prompt, create_quick_compatibility_prompt, call_llm_raw, parse_compatibility_response    
from services.github_service import get_user_by_id, get_user_recent_activity, get_user_repos as fetch_github_repos, get_user_starred_repos, get_user_topics, get_user_total_language_info
import asyncio      
import logging
import aiohttp
import datetime

router = APIRouter()

@router.get("/users/{user_name}")
async def get_user(user_name: str):
    try:
        return await get_user_by_id(user_name)
    except aiohttp.ClientResponseError as e:
        logging.error(f"GitHub API error fetching user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=e.status,
            detail=f"GitHub API error while fetching user '{user_name}': {e.message}"
        )
    except Exception as e:        
        logging.error(f"Error fetching user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching user '{user_name}': {str(e)}"
        )

@router.get("/users/{user_name}/repo_names")
async def get_user_repos(user_name: str):
    try:
        repo_name_list = []
        repos = await fetch_github_repos(user_name)
        for i in repos:
            repo_name_list.append(i['name'])
        return repo_name_list
    except aiohttp.ClientResponseError as e:
        logging.error(f"GitHub API error fetching repos for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=e.status,
            detail=f"GitHub API error while fetching repos for user '{user_name}': {e.message}"
        )
    except Exception as e:
        logging.error(f"Error fetching repos for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching repos for user '{user_name}': {str(e)}"
        )

@router.get("/users/{user_name}/languages")
async def get_user_languages(user_name: str):
    try:
        results = await get_user_total_language_info(user_name)
        return results
    except aiohttp.ClientResponseError as e:
        logging.error(f"GitHub API error fetching languages for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=e.status,
            detail=f"GitHub API error while fetching languages for user '{user_name}': {e.message}"
        )
    except Exception as e:
        logging.error(f"Error fetching languages for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching languages for user '{user_name}': {str(e)}"
        )

@router.get("/users/{user_name}/starred_repos")
async def get_starred_repos(user_name: str):
    try:
        return await get_user_starred_repos(user_name)
    except aiohttp.ClientResponseError as e:
        logging.error(f"GitHub API error fetching starred repos for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=e.status,
            detail=f"GitHub API error while fetching starred repos for user '{user_name}': {e.message}"
        )
    except Exception as e:
        logging.error(f"Error fetching starred repos for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching starred repos for user '{user_name}': {str(e)}"
        )

@router.get("/users/{user_name}/recent_activity")
async def get_recent_activity(user_name: str):
    try:
        return await get_user_recent_activity(user_name)
    except aiohttp.ClientResponseError as e:
        logging.error(f"GitHub API error fetching recent activity for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=e.status,
            detail=f"GitHub API error while fetching recent activity for user '{user_name}': {e.message}"
        )
    except Exception as e:
        logging.error(f"Error fetching recent activity for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching recent activity for user '{user_name}': {str(e)}"
        )

@router.get("/users/{user_name}/topics")
async def get_topics(user_name: str):
    try:
        return await get_user_topics(user_name)
    except aiohttp.ClientResponseError as e:
        logging.error(f"GitHub API error fetching topics for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=e.status,
            detail=f"GitHub API error while fetching topics for user '{user_name}': {e.message}"
        )
    except Exception as e:
        logging.error(f"Error fetching topics for user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching topics for user '{user_name}': {str(e)}"
        )

@router.post("/api/analyze-compatibility")
async def analyze_compatibility(request: UserCompatibilityRequest):
    """Main endpoint for compatibility analysis"""
    
    if len(request.usernames) < 2:
        raise HTTPException(status_code=400, detail="At least 2 usernames required")
    
    try:
        # Gather user profiles concurrently
        profile_tasks = [get_complete_user_info(username) for username in request.usernames]
        user_profiles = await asyncio.gather(*profile_tasks)
        
        # Generate LLM analysis
        llm_prompt = create_llm_prompt(user_profiles)
        llm_analysis = await call_llm_api(llm_prompt)
        
        # Generate metrics for visualization
        compatibility_metrics = analyze_compatibility_metrics(user_profiles)
        
        # Create enhanced response with structured data
        enhanced_response = {
            "success": True,
            "users": [profile.username for profile in user_profiles],
            "llm_analysis": llm_analysis,
            "compatibility_metrics": compatibility_metrics,
            "user_profiles": [profile.dict() for profile in user_profiles],
            "visualization_data": {
                "skills_overlap": {
                    "languages": compatibility_metrics.get("language_overlap", {}),
                    "compatibility_score": llm_analysis.analysis.compatibility_score if hasattr(llm_analysis.analysis, 'compatibility_score') else 5,
                    "compatibility_reasoning": llm_analysis.analysis.compatibility_reasoning if hasattr(llm_analysis.analysis, 'compatibility_reasoning') else "Analysis based on profile data"
                },
                "activity_comparison": {
                    profile.username: {
                        "pushes": len([a for a in profile.recent_activity if a['type'] == 'PushEvent']),
                        "prs": len([a for a in profile.recent_activity if a['type'] == 'PullRequestEvent']),
                        "repos": len(profile.repositories),
                        "original_repos": len([r for r in profile.repositories if not r['fork']])
                    } for profile in user_profiles
                },
                "project_ideas": llm_analysis.analysis.collaboration_opportunities if hasattr(llm_analysis.analysis, 'collaboration_opportunities') else []
            }
        }
        
        return enhanced_response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/api/quick-compatibility")
async def quick_compatibility(request: UserCompatibilityRequest):
    """Fast endpoint for just compatibility score and reasoning"""
    
    if len(request.usernames) < 2:
        raise HTTPException(status_code=400, detail="At least 2 usernames required")
    
    try:

        profile_tasks = [get_complete_user_info(username) for username in request.usernames]
        user_profiles = await asyncio.gather(*profile_tasks)
    
        quick_prompt = await create_quick_compatibility_prompt(user_profiles)
        
        raw_llm_response = await call_llm_raw(quick_prompt)
        
        compatibility_score, compatibility_reasoning = parse_compatibility_response(raw_llm_response)
        
        radar_chart_data = await create_radar_chart_data(user_profiles)
        
        return {
            "success": True,
            "users": [{"username": profile.username, "avatar_url": profile.avatar_url, "recent_activity": profile.recent_activity} for profile in user_profiles],
            "compatibility_score": compatibility_score,
            "compatibility_reasoning": compatibility_reasoning,
            "radar_chart_data": radar_chart_data,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"Quick compatibility failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick compatibility check failed: {str(e)}")

@router.get("/api/test-github-connection")
async def test_github_connection():
    """Test endpoint to verify GitHub API connectivity"""
    try:
        from services.github_graphql_service import GitHubGraphQLService
        
        service = GitHubGraphQLService()
        # Try a simple query to test connectivity
        test_query = """
        query {
            viewer {
                login
            }
        }
        """
        
        result = await service._execute_query(test_query)
        return {
            "success": True,
            "message": "GitHub GraphQL connection successful",
            "user": result.get("viewer", {}).get("login", "Unknown")
        }
    except Exception as e:
        logging.error(f"GitHub connection test failed: {str(e)}")
        return {
            "success": False,
            "message": f"GitHub connection failed: {str(e)}",
            "error": str(e)
        }

