from typing import List, Optional
from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, description="User query text")


class AskResponse(BaseModel):
    answer: str
    agents_used: List[str]
    rationale: str
    trace_id: Optional[str] = None


class UploadResponse(BaseModel):
    status: str
    file_id: str


class LogQuery(BaseModel):
    id: str
    timestamp: str
    query: str
    decision: dict
    agents_called: List[str]
    documents: List[dict]
    answer: str
    errors: Optional[List[str]] = None
