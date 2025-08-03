from google import genai
from google.genai import types
from models import UserProfile
from typing import List
import os
from fastapi import HTTPException
import asyncio

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

def create_llm_prompt(user_profiles: List[UserProfile]) -> str:
    """Create a structured prompt for the LLM"""
    
    prompt = """You are a GitHub collaboration analyzer. Analyze the following GitHub user profiles and provide insights on how these developers can work together effectively.

For each analysis, provide:
1. **Compatibility Score** (1-10): Overall collaboration potential
2. **Shared Strengths**: Common languages, topics, and interests
3. **Complementary Skills**: How their different skills can benefit each other
4. **Collaboration Opportunities**: Specific project ideas or areas where they could work together
5. **Potential Challenges**: Areas where they might face difficulties
6. **Recommendations**: Actionable advice for successful collaboration

Here are the user profiles:

"""
    
    for i, profile in enumerate(user_profiles, 1):
        prompt += f"""
## User {i}: {profile.username}

**Basic Info:**
- Public Repos: {profile.basic_info.get('public_repos', 'N/A')}
- Followers: {profile.basic_info.get('followers', 'N/A')}
- Following: {profile.basic_info.get('following', 'N/A')}
- Bio: {profile.basic_info.get('bio', 'No bio available')}
- Company: {profile.basic_info.get('company', 'N/A')}
- Location: {profile.basic_info.get('location', 'N/A')}

**Top Programming Languages:**
{', '.join([f"{lang} ({bytes:,} bytes)" for lang, bytes in profile.languages[:5]])}

**Top Topics/Technologies:**
{', '.join([f"{topic} ({count} repos)" for topic, count in profile.topics[:10]])}

**Recent Activity Summary:**
{len([activity for activity in profile.recent_activity if activity['type'] == 'PushEvent'])} recent pushes
{len([activity for activity in profile.recent_activity if activity['type'] == 'PullRequestEvent'])} recent pull requests
{len([activity for activity in profile.recent_activity if activity['type'] == 'IssuesEvent'])} recent issue activities

**Notable Starred Projects:**
{', '.join([f"{repo['name']} ({repo.get('language', 'Unknown')})" for repo in profile.starred_repos[:5] if repo.get('language')])}

**Repository Types:**
{len([repo for repo in profile.repositories if not repo['fork']])} original repositories
{len([repo for repo in profile.repositories if repo['fork']])} forked repositories

"""
    
    prompt += """
Please provide a comprehensive analysis focusing on practical collaboration opportunities and concrete next steps these developers could take to work together effectively.
"""
    
    return prompt




async def call_llm_api(prompt: str) -> str:
    """Call the Google Generative AI API (Gemini) asynchronously."""
    if not GOOGLE_API_KEY:
        raise HTTPException(status_code=500, detail="Google API key not set")

    client = genai.Client(api_key=GOOGLE_API_KEY)

    try:
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    max_output_tokens=2000
                )
            )
        )
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM API call failed: {str(e)}")
