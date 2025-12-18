"""
LLM Service - Async Gemini API integration with JSON output and dependency injection.
"""
import asyncio
import json
import logging
import re
from functools import lru_cache
from typing import List, Optional
import aiohttp
from fastapi import HTTPException
from jinja2 import Template
from pydantic import BaseModel, Field, field_validator
from models import UserProfile, CompatibilityFactor
from config.settings import get_settings

logger = logging.getLogger(__name__)

# Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Retry configuration
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 8.0  # seconds


class CompatibilityResponse(BaseModel):
    """Structured response from LLM compatibility analysis."""
    score: int = Field(..., ge=1, le=10, description="Compatibility score 1-10")
    reasoning: str = Field(..., min_length=10, description="2-3 sentence reasoning")
    compatibility_factors: List[CompatibilityFactor] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Exactly 4 compatibility factors"
    )
    
    @field_validator('score', mode='before')
    @classmethod
    def clamp_score(cls, v):
        """Ensure score is within valid range."""
        if isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                raise ValueError("Score must be a valid integer between 1-10")
        if not (1 <= v <= 10):
            raise ValueError(f"Score {v} must be between 1-10")
        return v


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
You are a GitHub compatibility analyst for GitM8. Analyze the developers and respond with ONLY valid JSON.

Output a JSON object with this EXACT structure:
{
  "score": <number 1-10>,
  "reasoning": "<2-3 sentences referencing users by name, explaining skill complementarity>",
  "compatibility_factors": [
    {
      "label": "Shared Languages",
      "indicator": "<1-2 sentence summary>"
    },
    {
      "label": "Project Sizes",
      "indicator": "<1-2 sentence summary>"
    },
    {
      "label": "Contribution Activity",
      "indicator": "<1-2 sentence summary>"
    },
    {
      "label": "Activity Heat",
      "indicator": "<1-2 sentence summary>"
    }
  ]
}

CRITICAL RULES:
- Output ONLY valid JSON (no markdown, no code blocks, no extra text)
- Score must be 1-10 (lean slightly optimistic)
- Reasoning must reference users by name
- Must include exactly 4 compatibility factors in the order shown
- Treat contrasts as positive collaboration opportunities

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


def create_quick_compatibility_prompt(user_profiles: List[UserProfile]) -> str:
    """Build quick compatibility prompt using cached Jinja2 template (synchronous - no I/O)."""
    template = _get_template("quick_compatibility")
    users = [_extract_user_data(p) for p in user_profiles]
    return template.render(users=users)


# =============================================================================
# ASYNC GEMINI CLIENT WITH DEPENDENCY INJECTION
# =============================================================================

class AsyncGeminiClient:
    """Async Gemini API client with retry logic and exponential backoff."""
    
    def __init__(self, session: aiohttp.ClientSession):
        """Initialize with an aiohttp session (injected via DI)."""
        self.session = session
        self.settings = get_settings()
    
    async def generate(
        self, 
        prompt: str, 
        temperature: float = 0.3, 
        max_tokens: int = 2000,
        max_retries: int = MAX_RETRIES
    ) -> str:
        """
        Generate content from Gemini API with retry logic and exponential backoff.
        
        Args:
            prompt: The prompt to send
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            max_retries: Maximum retry attempts for transient failures
            
        Returns:
            Generated text response
            
        Raises:
            HTTPException: On API errors or validation failures
        """
        if not self.settings.google_api_key:
            logger.error("Google API key not configured")
            raise HTTPException(
                status_code=500, 
                detail="GitM8 analysis service is not configured. Please contact support."
            )
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json"  # Request JSON output
            }
        }
        
        url = f"{GEMINI_API_URL}?key={self.settings.google_api_key}"
        
        last_exception = None
        retry_delay = INITIAL_RETRY_DELAY
        
        for attempt in range(max_retries):
            try:
                async with self.session.post(url, json=payload) as response:
                    if response.status == 200:
                        raw = await response.text()
                        
                        # Parse Gemini response
                        try:
                            data = json.loads(raw)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON from Gemini API: {raw[:500]}")
                            raise HTTPException(
                                status_code=502,
                                detail="GitM8 received an invalid response from the analysis service. Please try again."
                            )
                        
                        candidates = data.get("candidates", [])
                        if not candidates:
                            logger.warning(f"No candidates in Gemini response: {data}")
                            raise HTTPException(
                                status_code=502,
                                detail="GitM8 analysis service returned an empty response. Please try again."
                            )
                        
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        if not parts:
                            logger.warning(f"No parts in Gemini response: {content}")
                            raise HTTPException(
                                status_code=502,
                                detail="GitM8 analysis service returned an incomplete response. Please try again."
                            )
                        
                        finish_reason = candidates[0].get("finishReason", "")
                        if finish_reason == "MAX_TOKENS":
                            logger.warning("Response truncated due to MAX_TOKENS")
                            raise HTTPException(
                                status_code=502,
                                detail="GitM8 analysis was too complex and exceeded limits. Please try with fewer users."
                            )
                        
                        return parts[0].get("text", "")
                    
                    # Handle retryable errors (5xx, 429)
                    elif response.status in (429, 500, 502, 503, 504):
                        err = await response.text()
                        logger.warning(
                            f"Retryable error from Gemini (attempt {attempt + 1}/{max_retries}): "
                            f"status={response.status}, error={err[:200]}"
                        )
                        last_exception = HTTPException(
                            status_code=503,
                            detail="GitM8 analysis service is temporarily unavailable. Please try again in a moment."
                        )
                        
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                            continue
                    
                    # Non-retryable errors (4xx except 429)
                    else:
                        err = await response.text()
                        logger.error(f"Non-retryable Gemini API error {response.status}: {err}")
                        raise HTTPException(
                            status_code=502,
                            detail=f"GitM8 analysis service encountered an error (code: {response.status}). Please try again."
                        )
            
            except aiohttp.ClientError as e:
                logger.warning(
                    f"Network error calling Gemini (attempt {attempt + 1}/{max_retries}): {e}"
                )
                last_exception = HTTPException(
                    status_code=503,
                    detail="GitM8 couldn't reach the analysis service. Please check your connection and try again."
                )
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)
                    continue
            
            except HTTPException:
                # Re-raise HTTP exceptions immediately (no retry)
                raise
        
        # All retries exhausted
        if last_exception:
            raise last_exception
        
        raise HTTPException(
            status_code=503,
            detail="GitM8 analysis service is temporarily unavailable after multiple attempts. Please try again later."
        )


def parse_compatibility_response(raw_response: str) -> CompatibilityResponse:
    """
    Parse LLM JSON response to extract score, reasoning, and compatibility factors.
    Uses json.loads with regex fallback for robustness.
    
    Args:
        raw_response: Raw text response from LLM (should be JSON)
        
    Returns:
        Structured CompatibilityResponse
        
    Raises:
        HTTPException: If response cannot be parsed or is invalid
    """
    # Try to extract JSON if wrapped in markdown code blocks
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # Try to find raw JSON object
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = raw_response.strip()
    
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM JSON response: {raw_response[:500]}")
        raise HTTPException(
            status_code=502,
            detail="GitM8 received a malformed response from the analysis service. Please try again."
        )
    
    # Validate required fields
    if "score" not in data:
        logger.error(f"Missing 'score' in LLM response: {data}")
        raise HTTPException(
            status_code=502,
            detail="GitM8 analysis is incomplete (missing score). Please try again."
        )
    
    if "reasoning" not in data:
        logger.error(f"Missing 'reasoning' in LLM response: {data}")
        raise HTTPException(
            status_code=502,
            detail="GitM8 analysis is incomplete (missing reasoning). Please try again."
        )
    
    if "compatibility_factors" not in data:
        logger.error(f"Missing 'compatibility_factors' in LLM response: {data}")
        raise HTTPException(
            status_code=502,
            detail="GitM8 analysis is incomplete (missing factors). Please try again."
        )
    
    factors_data = data["compatibility_factors"]
    if not isinstance(factors_data, list) or len(factors_data) != 4:
        logger.error(f"Invalid compatibility_factors in LLM response: {factors_data}")
        raise HTTPException(
            status_code=502,
            detail="GitM8 analysis returned an unexpected format. Please try again."
        )
    
    # Parse compatibility factors
    try:
        factors = [
            CompatibilityFactor(
                label=f["label"],
                indicator=f["indicator"]
            )
            for f in factors_data
        ]
    except (KeyError, TypeError) as e:
        logger.error(f"Failed to parse compatibility factors: {e}, data={factors_data}")
        raise HTTPException(
            status_code=502,
            detail="GitM8 analysis contains invalid factor data. Please try again."
        )
    
    # Create and validate response
    try:
        return CompatibilityResponse(
            score=data["score"],
            reasoning=data["reasoning"],
            compatibility_factors=factors
        )
    except Exception as e:
        logger.error(f"Failed to validate CompatibilityResponse: {e}, data={data}")
        raise HTTPException(
            status_code=502,
            detail=f"GitM8 analysis validation failed: {str(e)}"
        )


# =============================================================================
# DEPENDENCY INJECTION HELPERS
# =============================================================================

_llm_client: Optional[AsyncGeminiClient] = None


async def init_llm_client(session: aiohttp.ClientSession):
    """Initialize LLM client with shared session (call in app startup)."""
    global _llm_client
    _llm_client = AsyncGeminiClient(session)
    logger.info("✅ LLM client initialized")


async def cleanup_llm_client():
    """Cleanup LLM client (call in app shutdown)."""
    global _llm_client
    _llm_client = None
    logger.info("✅ LLM client cleaned up")


def get_llm_client() -> AsyncGeminiClient:
    """
    Get LLM client instance (FastAPI dependency).
    
    Usage in routes:
        async def analyze(
            ...,
            llm_client: AsyncGeminiClient = Depends(get_llm_client)
        ):
            response = await llm_client.generate(prompt)
    """
    if _llm_client is None:
        logger.error("LLM client not initialized")
        raise HTTPException(
            status_code=503,
            detail="GitM8 analysis service is not ready. Please try again in a moment."
        )
    return _llm_client
