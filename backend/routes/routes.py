from fastapi import FastAPI, APIRouter, HTTPException
from services.github_service import get_user_by_id, get_user_recent_activity, get_user_repos as fetch_github_repos, get_user_starred_repos, get_user_topics, get_user_total_language_info
import asyncio      
import logging

router = APIRouter()

@router.get("/users/{user_name}")
async def get_user(user_name: str):
    # error handling
    try:
        return await get_user_by_id(user_name)
    except Exception as e:        
        logging.error(f"Error fetching user '{user_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching user '{user_name}': {str(e)}"
        )


@router.get("/users/{user_name}/repo_names")
async def get_user_repos(user_name: str):
    # need to return only the name of the repo by storing it in a list
    repo_name_list =[]
    for i in await fetch_github_repos(user_name):
        repo_name_list.append(i['name'])
    return repo_name_list

@router.get("/users/{user_name}/languages")
async def get_user_languages(user_name: str):
    results= await get_user_total_language_info(user_name)
    return results

@router.get("/users/{user_name}/starred_repos")
async def get_starred_repos(user_name: str):
    return await get_user_starred_repos(user_name)

@router.get("/users/{user_name}/recent_activity")
async def get_recent_activity(user_name: str):
    return await get_user_recent_activity(user_name)

@router.get("/users/{user_name}/topics")
async def get_topics(user_name: str):
    return await get_user_topics(user_name)