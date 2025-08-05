import asyncio
from fastapi import HTTPException
from services.github_service import (
    get_user_by_id, get_user_recent_activity, get_user_repos, 
    get_user_starred_repos, get_user_topics, get_user_total_language_info,
    get_user_expertise_analysis
)
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
        expertise_analysis_task = get_user_expertise_analysis(username)

        basic_info, languages, topics, starred_repos, recent_activity, repositories, expertise_analysis = await asyncio.gather(
            basic_info_task, languages_task, topics_task, 
            starred_repos_task, recent_activity_task, repositories_task,
            expertise_analysis_task
        )
        
        # Enhance basic_info with expertise analysis
        enhanced_basic_info = {
            **basic_info,
            'expertise_analysis': expertise_analysis
        }
        
        return UserProfile(
            username=username,
            basic_info=enhanced_basic_info,
            languages=languages,
            topics=topics,
            starred_repos=starred_repos,
            recent_activity=recent_activity,
            repositories=repositories,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user info: {str(e)}")
    
        
def analyze_compatibility_metrics(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """Generate numerical metrics for Chart.js visualization"""
    
    if len(user_profiles) < 2:
        return {}
    
    # Expertise-based compatibility analysis
    expertise_overlap = {}
    collaboration_potential = {}
    
    for profile in user_profiles:
        username = profile.username
        basic_info = profile.basic_info
        
        if 'expertise_analysis' in basic_info:
            expertise = basic_info['expertise_analysis']
            
            # Create expertise mapping
            expertise_overlap[username] = {
                'primary_expertise': expertise.get('primary_expertise', []),
                'collaboration_type': expertise.get('collaboration_type', 'Unknown'),
                'activity_consistency': expertise.get('activity_consistency', 0),
                'engagement_patterns': expertise.get('engagement_patterns', {})
            }
            
            # Calculate collaboration potential
            engagement = expertise.get('engagement_patterns', {})
            collaboration_potential[username] = {
                'project_initiator_ratio': engagement.get('project_initiator_ratio', 0),
                'contributor_ratio': engagement.get('contributor_ratio', 0),
                'active_projects': engagement.get('active_projects', 0),
                'recent_activity_score': engagement.get('recent_activity_score', 0)
            }
    
    # Language overlap analysis (keeping for backward compatibility)
    all_languages = set()
    user_languages = {}
    
    for profile in user_profiles:
        user_langs = {lang: bytes_count for lang, bytes_count in profile.languages}
        user_languages[profile.username] = user_langs
        all_languages.update(user_langs.keys())
    
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
        "user_topic_distribution": user_topics,
        "expertise_overlap": expertise_overlap,
        "collaboration_potential": collaboration_potential
    }