from fastapi import FastAPI, APIRouter
from controller.controller import get_user_by_id, get_user_repos as fetch_github_repos, get_user_total_language_info
import asyncio      

router = APIRouter()

@router.get("/users/{user_name}")
async def get_user(user_name: str):
    return await get_user_by_id(user_name)

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