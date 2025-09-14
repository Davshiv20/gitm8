from collections import defaultdict
from fastapi import FastAPI
import aiohttp
import asyncio
import os
from datetime import datetime
from config.settings import get_settings

settings = get_settings()
GITHUB_TOKEN = settings.github_token

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

# async def get_user_profile_picture(user_name: str):
#     url = f"https://api.github.com/users/{user_name}"
#     async with aiohttp.ClientSession(headers=HEADERS) as session:
#         async with session.get(url) as response:
#             response.raise_for_status()
#             return await response.json()['avatar_url']

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
            #get the name, description, and language of the repo and return in a dictionary
            repo_list = []
            for repo in await response.json():
                repo_list.append({
                    'name': repo['name'], 
                    'description': repo.get('description'),  # Use .get() to handle None
                    'language': repo.get('language')  # Use .get() to handle None
                })
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
async def get_user_contribution_stats(user_name: str):
    """Get detailed contribution statistics for a user"""
    url = f"https://api.github.com/users/{user_name}/events"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            events = await response.json()
            
            # Analyze contribution patterns
            event_types = defaultdict(int)
            repos_contributed_to = set()
            recent_activity = []
            
            for event in events[:50]:  # Last 50 events
                event_type = event['type']
                event_types[event_type] += 1
                repos_contributed_to.add(event['repo']['name'])
                recent_activity.append({
                    'type': event_type,
                    'repo': event['repo']['name'],
                    'created_at': event['created_at']
                })
            
            return {
                'event_breakdown': dict(event_types),
                'unique_repos_contributed': len(repos_contributed_to),
                'recent_activity': recent_activity,
                'total_events_analyzed': len(events[:50])
            }

async def get_user_repo_analysis(user_name: str):
    """Get detailed analysis of user's repositories"""
    repos = await get_user_repos(user_name)
    
    analysis = {
        'total_repos': len(repos),
        'original_repos': len([r for r in repos if not r['fork']]),
        'forked_repos': len([r for r in repos if r['fork']]),
        'avg_stars': sum(r['stargazers_count'] for r in repos) / len(repos) if repos else 0,
        'avg_forks': sum(r['forks_count'] for r in repos) / len(repos) if repos else 0,
        'most_starred_repo': max(repos, key=lambda x: x['stargazers_count']) if repos else None,
        'recent_repos': sorted(repos, key=lambda x: x['created_at'], reverse=True)[:5],
        'languages_used': list(set(r['language'] for r in repos if r['language'])),
        'repo_sizes': [r['size'] for r in repos],
        'has_readme_count': len([r for r in repos if r['has_wiki']]),
        'has_issues_count': len([r for r in repos if r['has_issues']])
    }
    
    return analysis

async def get_user_network_analysis(user_name: str):
    """Get network and collaboration patterns"""
    url = f"https://api.github.com/users/{user_name}"
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        async with session.get(url) as response:
            response.raise_for_status()
            user_data = await response.json()
            
            return {
                'followers_count': user_data['followers'],
                'following_count': user_data['following'],
                'public_repos': user_data['public_repos'],
                'public_gists': user_data['public_gists'],
                'account_age_days': (datetime.now() - datetime.fromisoformat(user_data['created_at'].replace('Z', '+00:00'))).days,
                'last_active': user_data['updated_at'],
                'hireable': user_data.get('hireable', False),
                'location': user_data.get('location'),
                'company': user_data.get('company'),
                'blog': user_data.get('blog')
            }

async def get_user_capability_analysis(user_name: str):
    """Analyze user capabilities based on activity patterns and project complexity"""
    repos = await get_user_repos(user_name)
    events = await get_user_recent_activity(user_name)
    
    # Analyze recent activity patterns
    recent_events = events[:30]  # Last 30 events
    event_types = defaultdict(int)
    repos_contributed = set()
    
    for event in recent_events:
        event_types[event['type']] += 1
        repos_contributed.add(event['repo'])
    
    # Analyze project complexity and engagement
    capability_metrics = {
        'activity_consistency': len(recent_events) / 30,  # Events per day
        'project_diversity': len(repos_contributed),
        'collaboration_style': {
            'pushes': event_types.get('PushEvent', 0),
            'pull_requests': event_types.get('PullRequestEvent', 0),
            'issues': event_types.get('IssuesEvent', 0),
            'reviews': event_types.get('PullRequestReviewEvent', 0)
        },
        'project_complexity': {},
        'technology_preferences': {},
        'engagement_patterns': {}
    }
    
    # Analyze each repository for complexity
    for repo in repos[:10]:  # Top 10 repos
        repo_name = repo['name']
        
        # Get repository details
        repo_url = f"https://api.github.com/repos/{user_name}/{repo_name}"
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(repo_url) as response:
                if response.status == 200:
                    repo_data = await response.json()
                    
                    # Calculate complexity metrics
                    complexity_score = 0
                    if repo_data.get('has_wiki'):
                        complexity_score += 1
                    if repo_data.get('has_issues'):
                        complexity_score += 1
                    if repo_data.get('has_projects'):
                        complexity_score += 1
                    if repo_data.get('has_downloads'):
                        complexity_score += 1
                    if repo_data.get('has_pages'):
                        complexity_score += 1
                    
                    # Language preference (not just lines of code)
                    if repo_data.get('language'):
                        lang = repo_data['language']
                        if lang not in capability_metrics['technology_preferences']:
                            capability_metrics['technology_preferences'][lang] = {
                                'repos_count': 0,
                                'complexity_score': 0,
                                'recent_activity': 0
                            }
                        
                        capability_metrics['technology_preferences'][lang]['repos_count'] += 1
                        capability_metrics['technology_preferences'][lang]['complexity_score'] += complexity_score
                        
                        # Check if this repo has recent activity
                        recent_activity = any(
                            event['repo'] == repo_name 
                            for event in recent_events
                        )
                        if recent_activity:
                            capability_metrics['technology_preferences'][lang]['recent_activity'] += 1
                    
                    capability_metrics['project_complexity'][repo_name] = {
                        'stars': repo_data.get('stargazers_count', 0),
                        'forks': repo_data.get('forks_count', 0),
                        'complexity_score': complexity_score,
                        'language': repo_data.get('language'),
                        'description': repo_data.get('description'),
                        'topics': await get_repo_topics(user_name, repo_name)
                    }
    
    # Calculate engagement patterns
    total_repos = len(repos)
    original_repos = len([r for r in repos if not r['fork']])
    forked_repos = len([r for r in repos if r['fork']])
    
    capability_metrics['engagement_patterns'] = {
        'project_initiator_ratio': original_repos / total_repos if total_repos > 0 else 0,
        'contributor_ratio': forked_repos / total_repos if total_repos > 0 else 0,
        'active_projects': len([r for r in repos if r['updated_at'] > '2024-01-01']),
        'recent_activity_score': len(recent_events) / 30
    }
    
    return capability_metrics

async def get_user_expertise_analysis(user_name: str):
    """Analyze user expertise based on project complexity and recent activity"""
    capability_metrics = await get_user_capability_analysis(user_name)
    
    # Determine primary expertise areas
    expertise_areas = []
    
    # Analyze technology preferences
    tech_prefs = capability_metrics['technology_preferences']
    for lang, metrics in tech_prefs.items():
        if metrics['repos_count'] >= 2 and metrics['recent_activity'] > 0:
            expertise_level = 'Expert' if metrics['complexity_score'] > 3 else 'Intermediate'
            expertise_areas.append({
                'language': lang,
                'level': expertise_level,
                'repos_count': metrics['repos_count'],
                'complexity_score': metrics['complexity_score'],
                'recent_activity': metrics['recent_activity']
            })
    
    # Sort by expertise level and activity
    expertise_areas.sort(key=lambda x: (x['complexity_score'], x['recent_activity']), reverse=True)
    
    # Analyze collaboration style
    collab_style = capability_metrics['collaboration_style']
    if collab_style['pull_requests'] > collab_style['pushes']:
        collaboration_type = 'Team Player'
    elif collab_style['pushes'] > 10:
        collaboration_type = 'Active Developer'
    else:
        collaboration_type = 'Occasional Contributor'
    
    return {
        'primary_expertise': expertise_areas[:5],  # Top 5 expertise areas
        'collaboration_type': collaboration_type,
        'activity_consistency': capability_metrics['activity_consistency'],
        'project_complexity': capability_metrics['project_complexity'],
        'engagement_patterns': capability_metrics['engagement_patterns']
    }
