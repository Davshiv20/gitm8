import asyncio
import logging
from fastapi import HTTPException
from services.github_graphql_service import get_complete_user_profile_graphql
from models import UserProfile
from typing import Dict, Any, List

async def get_complete_user_info(username: str) -> UserProfile:
    try:
        # Use GraphQL service exclusively
        user_data = await get_complete_user_profile_graphql(username)
        return UserProfile(
            username=user_data["username"],
            avatar_url=user_data["avatar_url"],
            basic_info=user_data["basic_info"],
            languages=user_data["languages"],
            topics=user_data["topics"],
            starred_repos=user_data["starred_repos"],
            recent_activity=user_data["recent_activity"],
            repositories=user_data["repositories"],
        )
    except Exception as e:
        logging.error(f"GraphQL service failed for {username}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching user info: {str(e)}")
    

async def create_radar_chart_data(user_profiles: List[UserProfile]) -> Dict[str, Any]:
    """
    Create radar chart data for the given user profiles.
    Returns a list of dicts like: {"language": "js", "shivam": 7, "ds": 0}
    Only the top 7 languages (by total usage across all users) are included.
    Instead of raw percentages, assigns reversed ranks per user (7 = most used, 1 = least used among top 7, 0 = not used).
    """
    # Convert profile.languages to dict if not already
    for profile in user_profiles:
        profile.languages = dict(profile.languages)

    # Aggregate total usage for each language across all users
    language_totals = {}
    for profile in user_profiles:
        for lang, count in profile.languages.items():
            language_totals[lang] = language_totals.get(lang, 0) + count

    # Pick top 7 languages by total usage
    top_languages = sorted(language_totals.items(), key=lambda x: x[1], reverse=True)[:10]
    top_language_names = [lang for lang, _ in top_languages]

    # For each user, assign reversed ranks to their languages (7 = most used, 1 = least used among top 7)
    user_language_ranks = {}
    for profile in user_profiles:

        user_top_langs = [(lang, count) for lang, count in profile.languages.items() if lang in top_language_names]
        sorted_langs = sorted(user_top_langs, key=lambda x: x[1], reverse=True)
        n = len(sorted_langs)
        ranks = {}
        for idx, (lang, _) in enumerate(sorted_langs):
            # Highest usage gets highest rank (n), next gets n-1, ..., lowest gets 1
            ranks[lang] = n - idx
        user_language_ranks[profile.username] = ranks

    # Prepare radar chart data for only the top 7 languages, using reversed ranks
    radar_data = []
    for lang in top_language_names:
        lang_entry = {"language": lang}
        for profile in user_profiles:
            ranks = user_language_ranks.get(profile.username, {})
            lang_entry[profile.username] = ranks.get(lang, 0)  # 0 if not present
        radar_data.append(lang_entry)

    return {"languages": radar_data}
        
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