import os
import asyncio
from typing import List, Protocol, Any
from fastapi import HTTPException
from models import UserProfile, CollaborationInsight
from google import genai

class LLMClient(Protocol):
    async def generate(self, prompt: str, output_schema: Any) -> Any:
        ...

class GoogleGeminiClient:
    def __init__(self, api_key: str):
        self.genai = genai
        self.api_key = api_key
        self.client = self.genai.Client(api_key=api_key)

    async def generate(self, prompt: str, output_schema: Any) -> Any:
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model="gemini-2.0-flash-lite",
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": output_schema,
                        "temperature": 0.3,
                        "max_output_tokens": 1500
                    }
                )
            )
            
            # Check if response and parsed content exist
            if not response or not hasattr(response, 'parsed') or response.parsed is None:
                raise Exception("Invalid response from Gemini API")
                
            return response.parsed
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"LLM API call failed: {str(e)}")

class LLMClientFactory:
    @staticmethod
    def get_client(provider: str = "google_gemini") -> LLMClient:
        if provider == "google_gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="Google API key not set")
            return GoogleGeminiClient(api_key)
        raise HTTPException(status_code=500, detail=f"Unknown LLM provider: {provider}")

class PromptBuilder(Protocol):
    def build(self, user_profiles: List[UserProfile]) -> str:
        ...


class CollaborationPromptBuilder:
    def build(self, user_profiles: List[UserProfile]) -> str:
        prompt = """You are an expert GitHub collaboration analyst. Your goal is to provide SPECIFIC, ACTIONABLE insights that developers can immediately act upon.

Analyze these developers and provide:

1. **Compatibility Score** (1-10): With 3 lines of critical reasoning based on their actual GitHub data and in a way that interests users in knowing more about their compatibility.
3. **Complementary Skills**: How their different expertise creates unique value propositions
4. **Collaboration Opportunities**: 3-5 SPECIFIC project ideas with:
   - Project name and description
   - Required skills (matching their profiles)
   - Estimated timeline (2-4 weeks, 1-3 months, 3-6 months)
   - Market potential or learning value
5. **Potential Challenges**: Specific obstacles with concrete solutions
6. **Recommendations**: Step-by-step action plan with immediate next steps

IMPORTANT: Be specific about technologies, frameworks, and project details. Don't give generic advice.

Here are the user profiles:

"""
        for i, profile in enumerate(user_profiles, 1):
            original_repos = len([repo for repo in profile.repositories if not repo['fork']])
            forked_repos = len([repo for repo in profile.repositories if repo['fork']])
            push_events = len([activity for activity in profile.recent_activity if activity['type'] == 'PushEvent'])
            pr_events = len([activity for activity in profile.recent_activity if activity['type'] == 'PullRequestEvent'])
            top_languages = [f"{lang} ({bytes:,} bytes)" for lang, bytes in profile.languages[:3]]
            top_topics = [f"{topic} ({count} repos)" for topic, count in profile.topics[:5]]

            prompt += f"""
## User {i}: {profile.username}

**Profile:**
- Public Repos: {profile.basic_info.get('public_repos', 'N/A')} (Original: {original_repos}, Forked: {forked_repos})
- Followers: {profile.basic_info.get('followers', 'N/A')}
- Bio: {profile.basic_info.get('bio', 'No bio available')}
- Company: {profile.basic_info.get('company', 'N/A')}

**Expertise Analysis:**
"""
            if 'expertise_analysis' in profile.basic_info:
                expertise = profile.basic_info['expertise_analysis']
                prompt += f"""
- Collaboration Type: {expertise.get('collaboration_type', 'Unknown')}
- Activity Consistency: {expertise.get('activity_consistency', 0):.2f} events/day
- Primary Expertise Areas:
"""
                for exp in expertise.get('primary_expertise', [])[:3]:
                    prompt += f"  • {exp['language']} ({exp['level']}) - {exp['repos_count']} repos, complexity: {exp['complexity_score']}\n"
                engagement = expertise.get('engagement_patterns', {})
                prompt += f"""
- Project Initiator Ratio: {engagement.get('project_initiator_ratio', 0):.1%}
- Active Projects: {engagement.get('active_projects', 0)}
- Recent Activity Score: {engagement.get('recent_activity_score', 0):.2f}
"""
            else:
                prompt += f"""
- Top Languages: {', '.join(top_languages)}
- Top Technologies: {', '.join(top_topics)}
- Activity: {push_events} pushes, {pr_events} PRs
- Activity Level: {'High' if push_events > 10 else 'Medium' if push_events > 5 else 'Low'}
"""

            prompt += f"""
**Development Style:**
- {'Project initiator' if original_repos > forked_repos else 'Contributor-focused' if forked_repos > original_repos else 'Balanced'}
- {'Community-engaged' if pr_events > 5 else 'Code-focused'}

**Notable Starred Projects:**
{', '.join([f"{repo['name']} ({repo.get('language', 'Unknown')})" for repo in profile.starred_repos[:3] if repo.get('language')])}

"""
        prompt += """
CRITICAL REQUIREMENTS:
1. Give SPECIFIC project names and descriptions
2. Mention exact technologies they should use based on their profiles
3. Provide realistic timelines and milestones
4. Suggest immediate next steps (first week, first month)
5. Identify potential revenue or learning opportunities
6. Be specific about who does what in each project

Make your analysis immediately actionable with concrete steps.
"""
        return prompt

class PromptBuilderFactory:
    @staticmethod
    def get_builder(task_type: str = "collaboration") -> PromptBuilder:
        if task_type == "collaboration":
            return CollaborationPromptBuilder()
        raise HTTPException(status_code=500, detail=f"Unknown prompt builder type: {task_type}")

# Facade for LLM Service
class LLMService:
    def __init__(self, provider: str = "google_gemini", prompt_type: str = "collaboration"):
        self.llm_client = LLMClientFactory.get_client(provider)
        self.prompt_builder = PromptBuilderFactory.get_builder(prompt_type)

    def create_prompt(self, user_profiles: List[UserProfile]) -> str:
        return self.prompt_builder.build(user_profiles)

    async def analyze_collaboration(self, user_profiles: List[UserProfile]) -> CollaborationInsight:
        prompt = self.create_prompt(user_profiles)
        result = await self.llm_client.generate(prompt, CollaborationInsight)
        return result

def create_llm_prompt(user_profiles: List[UserProfile]) -> str:
    return CollaborationPromptBuilder().build(user_profiles)

async def call_llm_api(prompt: str) -> CollaborationInsight:
    service = LLMService()
    return await service.llm_client.generate(prompt, CollaborationInsight)
