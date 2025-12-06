"""
LLM Service - Async Gemini API integration with Jinja2 templated prompts.
"""
import logging
import aiohttp
import re
from functools import lru_cache
from typing import List
from fastapi import HTTPException
from jinja2 import Template
from pydantic import BaseModel, Field, field_validator
from models import UserProfile, CompatibilityFactor
from config.settings import get_settings


class CompatibilityResponse(BaseModel):
    """Structured response from LLM compatibility analysis (internal parsing)."""
    score: int = Field(default=5, ge=1, le=10, description="Compatibility score 1-10")
    reasoning: str = Field(default="Analysis based on profile data", description="2-3 sentence reasoning")
    compatibility_factors: List[CompatibilityFactor] = Field(
        default_factory=list,
        description="List of 4 compatibility factors"
    )
    
    @field_validator('score', mode='before')
    @classmethod
    def clamp_score(cls, v):
        """Ensure score is within valid range."""
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                return 5
        return max(1, min(10, v))

logger = logging.getLogger(__name__)

# Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-lite:generateContent"


# =============================================================================
# JINJA2 TEMPLATES (LRU cached)
# =============================================================================

@lru_cache(maxsize=4)
def _get_template(template_name: str) -> Template:
    """Get compiled Jinja2 template (cached)."""
    templates = {
        "collaboration": Template("""
        You are an expert GitHub collaboration analyst. Provide SPECIFIC, ACTIONABLE insights.

Analyze these developers and provide:
1. **Compatibility Score** (1-10): With 3 lines of critical reasoning
2. **Complementary Skills**: How their different expertise creates value
3. **Collaboration Opportunities**: 3-5 SPECIFIC project ideas with:
   - Project name and description
   - Required skills (matching their profiles)
   - Estimated timeline
   - Market potential or learning value
4. **Potential Challenges**: Specific obstacles with solutions
5. **Recommendations**: Step-by-step action plan

IMPORTANT: Be specific about technologies, frameworks, and project details.

User Profiles:
{% for user in users %}
## User {{ loop.index }}: {{ user.username }}
- Repos: {{ user.public_repos }} (Original: {{ user.original_repos }}, Forked: {{ user.forked_repos }})
- Followers: {{ user.followers }}
- Bio: {{ user.bio or 'N/A' }}
- Company: {{ user.company or 'N/A' }}
- Languages: {{ user.top_langs }}
- Topics: {{ user.top_topics }}
- Activity: {{ user.push_events }} pushes, {{ user.pr_events }} PRs
{% if user.expertise %}- Type: {{ user.expertise.collaboration_type }}
{% for exp in user.expertise.primary_expertise[:3] %}  • {{ exp.language }} ({{ exp.level }}) - {{ exp.repos_count }} repos
{% endfor %}{% endif %}
{% endfor %}"""),

        "quick_compatibility": Template("""
You are a GitHub compatibility analyst. Analyze the developers and output ONLY:

1. **Compatibility Score (1–10)** — lean slightly optimistic.
2. **Compatibility Reasoning** — 2–3 sentences referencing the users by name and explaining why their skills complement each other. Treat contrasts as positive.
3. **Key Compatibility Factors** — return exactly 4 bullet points with SHORT explanations:
   - **Shared Languages:** one-line explanation
   - **Project Sizes:** one-line explanation
   - **Contribution Activity:** one-line explanation
   - **Activity Heat:** one-line explanation

STRICT OUTPUT FORMAT (NO deviation):
Score: [number]
Reasoning: [2–3 sentences]
Key Compatibility Factors:
- Shared Languages: [explanation]
- Project Sizes: [explanation]
- Contribution Activity: [explanation]
- Activity Heat: [explanation]

User Profiles:
{% for user in users %}
## User {{ loop.index }}: {{ user.username }}
- Repos: {{ user.public_repos }} (Original: {{ user.original_repos }}, Forked: {{ user.forked_repos }})
- Followers: {{ user.followers }}
- Languages: {{ user.top_langs }}
- Bio: {{ user.bio or 'No bio available' }}
- Topics: {{ user.top_topics }}
- Activity: {{ user.push_events }} pushes, {{ user.pr_events }} PRs
{% if user.expertise %}- Type: {{ user.expertise.collaboration_type }}
{% for exp in user.expertise.primary_expertise[:3] %}  • {{ exp.language }} ({{ exp.level }}) - {{ exp.repos_count }} repos
{% endfor %}{% endif %}
{% endfor %}


Return ONLY the formatted output above. No extra text.
""")

    }
    return templates[template_name]


def _extract_user_data(profile: UserProfile) -> dict:
    """Extract user data for template rendering."""
    repos = profile.repositories or []
    activities = profile.recent_activity or []
    
    original_repos = sum(1 for r in repos if not r.get('fork', False))
    
    return {
        "username": profile.username,
        "public_repos": profile.basic_info.get('public_repos', 0),
        "original_repos": original_repos,
        "forked_repos": len(repos) - original_repos,
        "followers": profile.basic_info.get('followers', 0),
        "bio": profile.basic_info.get('bio'),
        "company": profile.basic_info.get('company'),
        "top_langs": ', '.join(f"{lang} ({b:,}B)" for lang, b in profile.languages[:3]),
        "top_topics": ', '.join(f"{t} ({c})" for t, c in profile.topics[:5]),
        "push_events": sum(1 for a in activities if a.get('type') == 'PushEvent'),
        "pr_events": sum(1 for a in activities if a.get('type') == 'PullRequestEvent'),
        "expertise": profile.basic_info.get('expertise_analysis'),
    }


def create_llm_prompt(user_profiles: List[UserProfile]) -> str:
    """Build collaboration analysis prompt using cached Jinja2 template."""
    template = _get_template("collaboration")
    users = [_extract_user_data(p) for p in user_profiles]
    return template.render(users=users)


async def create_quick_compatibility_prompt(user_profiles: List[UserProfile]) -> str:
    """Build quick compatibility prompt using cached Jinja2 template."""
    template = _get_template("quick_compatibility")
    users = [_extract_user_data(p) for p in user_profiles]
    return template.render(users=users)


# =============================================================================
# ASYNC GEMINI CLIENT
# =============================================================================

class AsyncGeminiClient:
    """Pure async Gemini API client using aiohttp."""
    
    _instance = None
    _session: aiohttp.ClientSession = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def get_session(cls) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if cls._session is None or cls._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=5)
            cls._session = aiohttp.ClientSession(timeout=timeout)
        return cls._session
    
    @classmethod
    async def close(cls):
        """Close the session."""
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None
    
    async def generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 500) -> str:
        """Generate content from Gemini API."""
        settings = get_settings()
        if not settings.google_api_key:
            raise HTTPException(status_code=500, detail="Google API key not configured")
        
        session = await self.get_session()
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            }
        }
        
        url = f"{GEMINI_API_URL}?key={settings.google_api_key}"
        
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Gemini API error {response.status}: {error_text}")
                    raise HTTPException(status_code=502, detail=f"Gemini API error: {response.status}")
                
                data = await response.json()
                
                # Extract text from response
                candidates = data.get("candidates", [])
                if not candidates:
                    raise HTTPException(status_code=502, detail="No response from Gemini")
                
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    raise HTTPException(status_code=502, detail="Empty response from Gemini")
                
                return parts[0].get("text", "")
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Gemini: {e}")
            raise HTTPException(status_code=503, detail="LLM service unavailable")


# Singleton instance
_gemini = AsyncGeminiClient()


async def call_llm_raw(prompt: str) -> str:
    """Call Gemini API asynchronously."""
    return await _gemini.generate(prompt)


def parse_compatibility_response(raw_response: str) -> CompatibilityResponse:
    """
    Parse LLM response to extract score, reasoning, and compatibility factors.
    Returns a structured Pydantic model.

    Expected format:
        Score: <int>
        Reasoning: <string>
        Key Compatibility Factors:
        - Shared Languages: <explanation>
        - Project Sizes: <explanation>
        - Contribution Activity: <explanation>
        - Activity Heat: <explanation>
    """
    # Default values
    score = 5
    reasoning = "Analysis based on profile data"
    factors: List[CompatibilityFactor] = []
    
    # Known factor labels in expected order
    FACTOR_LABELS = [
        "Shared Languages",
        "Project Sizes", 
        "Contribution Activity",
        "Activity Heat"
    ]

    try:
        lines = raw_response.strip().split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Parse score
            if line_stripped.startswith('Score:'):
                try:
                    score_str = line_stripped.split(':', 1)[1].strip()
                    # Handle cases like "8/10" or just "8"
                    score_match = re.match(r'(\d+)', score_str)
                    if score_match:
                        score = int(score_match.group(1))
                except (ValueError, IndexError):
                    pass
            
            # Parse reasoning
            elif line_stripped.startswith('Reasoning:'):
                reasoning = line_stripped.split(':', 1)[1].strip()
            
            # Parse compatibility factors
            elif line_stripped.startswith('-'):
                # Remove leading dash and whitespace
                factor_text = line_stripped.lstrip('-').strip()
                
                # Check if this matches one of our known labels
                # Format: "Label: explanation" or "**Label:** explanation"
                for label in FACTOR_LABELS:
                    # Handle both "Label:" and "**Label:**" formats
                    patterns = [
                        f"**{label}:**",
                        f"**{label}**:",
                        f"{label}:",
                    ]
                    
                    for pattern in patterns:
                        if factor_text.startswith(pattern):
                            explanation = factor_text[len(pattern):].strip()
                            factors.append(CompatibilityFactor(
                                label=label,
                                explanation=explanation
                            ))
                            break
                    else:
                        continue
                    break  # Found a match, stop checking patterns
                    
    except Exception as e:
        logger.warning(f"Failed to parse LLM response: {e}")
    
    # Ensure we have all 4 factors with defaults if missing
    existing_labels = {f.label for f in factors}
    for label in FACTOR_LABELS:
        if label not in existing_labels:
            factors.append(CompatibilityFactor(
                label=label,
                explanation="Data not available"
            ))
    
    # Sort factors to match expected order
    factors_sorted = sorted(
        factors, 
        key=lambda f: FACTOR_LABELS.index(f.label) if f.label in FACTOR_LABELS else 99
    )
    
    return CompatibilityResponse(
        score=score,
        reasoning=reasoning,
        compatibility_factors=factors_sorted
    )


# Cleanup function for app shutdown
async def cleanup_llm_client():
    """Close the async client session."""
    await AsyncGeminiClient.close()
