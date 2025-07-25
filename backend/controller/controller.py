from collections import defaultdict
from fastapi import FastAPI
import aiohttp
import asyncio
#this is controller for the backend

async def get_user_by_id(user_name: str):
    url = f"https://api.github.com/users/{user_name}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

async def get_user_repos(user_name: str):
    url = f"https://api.github.com/users/{user_name}/repos"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

async def get_loc_in_respective_languages(user_name: str, repo_name: str):
    url = f"https://api.github.com/repos/{user_name}/{repo_name}/languages"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

async def get_user_total_language_info(user_name: str):
    repo_list = await get_user_repos(user_name)
    tasks = [get_loc_in_respective_languages(user_name, repo['name']) for repo in repo_list]
    results = await asyncio.gather(*tasks)

    total = defaultdict(int)
    for result in results:
        for language, loc in result.items():
            total[language] += loc
    return total
    