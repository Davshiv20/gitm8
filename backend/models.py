# pydantic classes for the backend
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel

class UserCompatibilityRequest(BaseModel):
    usernames: list[str]

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
    recent_activity: Optional[List[Dict[str, str]]]
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