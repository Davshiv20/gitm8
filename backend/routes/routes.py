"""
API Routes for compatibility analysis.
"""
from fastapi import APIRouter, HTTPException
from models import (
    UserCompatibilityRequest, 
    QuickCompatibilityResponse,
    QuickCompatibilityUser,
    CompatibilityFactor
)
from services.analytics_service import get_users_batch, UserProfileAnalyzer
from services.llm_service import create_llm_prompt, create_quick_compatibility_prompt, call_llm_raw, parse_compatibility_response
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/analyze-compatibility")
async def analyze_compatibility(request: UserCompatibilityRequest):
    """Main endpoint for compatibility analysis."""
    if len(request.usernames) < 2:
        raise HTTPException(status_code=400, detail="At least 2 usernames required")
    
    try:
        # Fetch ALL users in SINGLE API call (much faster than individual calls)
        user_profiles = await get_users_batch(request.usernames)
        
        # Create analyzer ONCE - all calculations done here
        analyzer = UserProfileAnalyzer(user_profiles)
        
        # Generate LLM prompt (if needed)
        llm_prompt = create_llm_prompt(user_profiles)
        # llm_analysis = await call_llm_api(llm_prompt)
        
        # Get all metrics from cached analyzer
        compatibility_metrics = analyzer.get_compatibility_metrics()
        
        return {
            "success": True,
            "users": [profile.username for profile in user_profiles],
            # "llm_analysis": llm_analysis,
            "compatibility_metrics": compatibility_metrics,
            "user_profiles": [profile.dict() for profile in user_profiles],
            "visualization_data": {
                "skills_overlap": {
                    "languages": compatibility_metrics.get("language_overlap", {}),
                },
                "activity_comparison": {
                    username: analyzer.get_user_summary(username)["activity"]
                    for username in [p.username for p in user_profiles]
                },
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/api/quick-compatibility", response_model=QuickCompatibilityResponse)
async def quick_compatibility(request: UserCompatibilityRequest) -> QuickCompatibilityResponse:
    """Fast endpoint for compatibility score and reasoning."""
    if len(request.usernames) < 2:
        raise HTTPException(status_code=400, detail="At least 2 usernames required")
    
    try:
        # Fetch ALL users in SINGLE API call (much faster than individual calls)
        user_profiles = await get_users_batch(request.usernames)
        
        # Create analyzer ONCE - all calculations cached
        analyzer = UserProfileAnalyzer(user_profiles)
        
        # LLM analysis - returns structured Pydantic model
        quick_prompt = await create_quick_compatibility_prompt(user_profiles)
        raw_llm_response = await call_llm_raw(quick_prompt)
        compatibility_result = parse_compatibility_response(raw_llm_response)
        
        # Get all chart data from SAME cached analyzer
        radar_chart_data = analyzer.get_radar_chart_data()
        comparison_data = analyzer.get_comparison_metrics()
        
        # Build structured Pydantic response
        return QuickCompatibilityResponse(
            success=True,
            users=[
                QuickCompatibilityUser(
                    username=profile.username,
                    avatar_url=profile.avatar_url,
                    recent_activity=profile.recent_activity
                )
                for profile in user_profiles
            ],
            compatibility_score=compatibility_result.score,
            compatibility_reasoning=compatibility_result.reasoning,
            compatibility_factors=[
                CompatibilityFactor(label=f.label, explanation=f.explanation)
                for f in compatibility_result.compatibility_factors
            ],
            radar_chart_data=radar_chart_data,
            comparison_data=comparison_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick compatibility failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Quick compatibility check failed: {str(e)}")


@router.get("/api/test-github-connection")
async def test_github_connection():
    """Test endpoint to verify GitHub API connectivity."""
    try:
        from services.github_graphql_service import GitHubGraphQLService
        
        service = GitHubGraphQLService()
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
        logger.error(f"GitHub connection test failed: {str(e)}")
        return {
            "success": False,
            "message": f"GitHub connection failed: {str(e)}",
            "error": str(e)
        }
