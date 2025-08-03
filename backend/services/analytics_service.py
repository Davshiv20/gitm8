import asyncio
from fastapi import HTTPException
from services.github_service import get_user_by_id, get_user_recent_activity, get_user_repos, get_user_starred_repos, get_user_topics, get_user_total_language_info
from models import UserProfile
from typing import Dict, Any, List
async def get_complete_user_info(username: str)-> UserProfile:
    try:
        basic_info_task= get_user_by_id(username)
        languages_task = get_user_total_language_info(username)
        topics_task = get_user_topics(username)
        starred_repos_task = get_user_starred_repos(username)
        recent_activity_task = get_user_recent_activity(username)
        repositories_task = get_user_repos(username)

        basic_info, languages, topics, starred_repos, recent_activity, repositories = await asyncio.gather(
            basic_info_task, languages_task, topics_task, 
            starred_repos_task, recent_activity_task, repositories_task
        )
        return UserProfile(
            username=username,
            basic_info=basic_info,
            languages=languages,
            topics=topics,
            starred_repos=starred_repos,
            recent_activity=recent_activity,
            repositories=repositories
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user info: {str(e)}")
    
        
def analyze_compatibility_metrics(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """Generate numerical metrics for Chart.js visualization"""
    
    if len(user_profiles) < 2:
        return {}
    
    # Language overlap analysis
    all_languages = set()
    user_languages = {}
    
    for profile in user_profiles:
        user_langs = {lang: bytes_count for lang, bytes_count in profile.languages}
        user_languages[profile.username] = user_langs
        all_languages.update(user_langs.keys())
    
    # Calculate language similarity
    common_languages = []
    language_overlap = {}
    
    for lang in all_languages:
        users_with_lang = [user for user in user_languages if lang in user_languages[user]]
        if len(users_with_lang) > 1:
            common_languages.append(lang)
            language_overlap[lang] = len(users_with_lang)
    
    # Topic overlap analysis
    all_topics = set()
    user_topics = {}
    
    for profile in user_profiles:
        user_topic_set = {topic: count for topic, count in profile.topics}
        user_topics[profile.username] = user_topic_set
        all_topics.update(user_topic_set.keys())
    
    common_topics = []
    topic_overlap = {}
    
    for topic in all_topics:
        users_with_topic = [user for user in user_topics if topic in user_topics[user]]
        if len(users_with_topic) > 1:
            common_topics.append(topic)
            topic_overlap[topic] = len(users_with_topic)
    
    return {
        "language_overlap": language_overlap,
        "topic_overlap": topic_overlap,
        "common_languages": common_languages,
        "common_topics": common_topics,
        "user_language_distribution": user_languages,
        "user_topic_distribution": user_topics
    }