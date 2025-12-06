# pydantic classes for the backend
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime


class UserCompatibilityRequest(BaseModel):
    usernames: list[str]

class CompatibilityFactor(BaseModel):
    """A single compatibility factor with label and explanation."""
    label: str = Field(..., description="Factor name (e.g., 'Shared Languages')")
    explanation: str = Field(..., description="One-line explanation of this factor")


class QuickCompatibilityUser(BaseModel):
    """User info returned in quick compatibility response."""
    username: str
    avatar_url: str
    recent_activity: Optional[List[Dict[str, Any]]] = None


class QuickCompatibilityResponse(BaseModel):
    """Structured response for /api/quick-compatibility endpoint."""
    success: bool = True
    users: List[QuickCompatibilityUser]
    compatibility_score: int = Field(..., ge=1, le=10, description="Compatibility score 1-10")
    compatibility_reasoning: str = Field(..., description="2-3 sentence reasoning")
    compatibility_factors: List[CompatibilityFactor] = Field(
        ..., 
        description="List of 4 compatibility factors"
    )
    radar_chart_data: Dict[str, Any] = Field(default_factory=dict)
    comparison_data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class UserCompatibilityResponse(BaseModel):
    username: str
    basic_info: Dict[str, Any]
    languages: List[str]
    topics: List[str]
    starred_repos: Optional[List[Dict[str, Any]]]
    recent_activity: Optional[List[Dict[str, str]]]
    repositories: List[Dict[str, Any]]

class UserProfile(BaseModel):
    username: str
    avatar_url: str
    basic_info: Dict[str, Any]
    languages: List[tuple]
    topics: List[tuple]
    starred_repos: Optional[List[Dict[str, Union[str, None]]]]
    recent_activity: Optional[List[Dict[str, Any]]]
    repositories: List[Dict[str, Any]]
    # profile_picture: str

class ProjectIdea(BaseModel):
    name: str
    description: str
    required_skills: List[str]
    timeline: str
    market_potential: str
    roles: str

class CollaborationAnalysis(BaseModel):
    compatibility_score: int
    compatibility_reasoning: str
    shared_strengths: List[str]
    complementary_skills: List[str]
    collaboration_opportunities: List[str]
    potential_challenges: List[str]
    recommendations: List[str]
    summary: str

class CollaborationInsight(BaseModel):
    analysis: CollaborationAnalysis
    key_insights: List[str]
    next_steps: List[str]