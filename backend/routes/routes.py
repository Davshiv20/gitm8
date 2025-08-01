from fastapi import FastAPI, APIRouter, HTTPException
from services.github_service import get_user_by_id, get_user_recent_activity, get_user_repos as fetch_github_repos, get_user_starred_repos, get_user_topics, get_user_total_language_info
import asyncio      
import logging
import aiohttp

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