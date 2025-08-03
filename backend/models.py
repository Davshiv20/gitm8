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
    basic_info: Dict[str, Any]
    languages: List[tuple]
    topics: List[tuple]
    starred_repos: Optional[List[Dict[str, Union[str, None]]]]
    recent_activity: Optional[List[Dict[str, str]]]
    repositories: List[Dict[str, Any]]