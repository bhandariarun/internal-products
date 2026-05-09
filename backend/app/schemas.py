from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    # role is NOT accepted from client

class UserResponse(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: EmailStr
    role: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[str] = None

class ScoreCreate(BaseModel):
    category: str
    score: int = Field(..., ge=1, le=5)
    note: Optional[str] = None

class ScoreResponse(ScoreCreate):
    id: str
    reviewer_id: str
    created_at: datetime

class CandidateResponse(BaseModel):
    id: str
    name: str
    email: str
    role_applied: str
    status: str
    skills: List[str]
    created_at: datetime
    # We will exclude internal_notes for non-admins dynamically or via separate schema

class CandidateDetailResponse(CandidateResponse):
    scores: List[ScoreResponse] = []
    internal_notes: Optional[str] = None

class PaginatedCandidates(BaseModel):
    items: List[CandidateResponse]
    total: int
    page: int
    page_size: int
