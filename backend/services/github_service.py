from collections import defaultdict
from fastapi import FastAPI
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

async def get_user_by_id(user_name: str):
    url = f"https://api.github.com/users/{user_name}"
   
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

async def get_user_repos(user_name: str):
    url = f"https://api.github.com/users/{user_name}/repos"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.json()

async def get_loc_in_respective_languages(user_name: str, repo_name: str):
    url = f"https://api.github.com/repos/{user_name}/{repo_name}/languages"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
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

    sorted_total = sorted(total.items(), key=lambda x: x[1], reverse=True)
    return sorted_total
    
async def get_repo_topics(user_name: str, repo_name: str):
    """Get topics for a specific repository"""
    url = f"https://api.github.com/repos/{user_name}/{repo_name}/topics"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get('names', [])

async def get_user_topics(user_name: str):
    """Get all topics from user's repositories with frequency count"""
    repo_list = await get_user_repos(user_name)
    
    # Get topics for all repositories concurrently
    tasks = [get_repo_topics(user_name, repo['name']) for repo in repo_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Aggregate topics with frequency count
    topic_frequency = defaultdict(int)
    for topics in results:
        if isinstance(topics, list):  # Skip any exceptions
            for topic in topics:
                topic_frequency[topic] += 1
    
    # Sort by frequency (most common topics first)
    sorted_topics = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)
    return sorted_topics

async def get_user_starred_repos(user_name:str):
    url = f"https://api.github.com/users/{user_name}/starred"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            #get the name and description of the repo and return in a dictionary
            repo_list = []
            for repo in await response.json():
                repo_list.append({'name': repo['name'], 'description': repo['description']})
            return repo_list

async def get_user_recent_activity(user_name:str):
    url = f"https://api.github.com/users/{user_name}/events"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            # classify the events into push, pull request, issue, etc.
            event_list = []
            for event in await response.json():
                event_list.append({'type': event['type'], 'repo': event['repo']['name'], 'created_at': event['created_at']})
            return event_list