from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any


Grade = Literal["Junior", "Middle", "Senior"]
HiringRecommendation = Literal["No Hire", "Hire", "Strong Hire"]
EvalLabel = Literal["correct", "partial", "wrong", "unknown"]


class CandidateProfile(BaseModel):
    participant_name: str
    position: str
    target_grade: Grade
    experience: str


class TurnLog(BaseModel):
    turn_id: int
    agent_visible_message: str
    user_message: str
    internal_thoughts: str


class GapItem(BaseModel):
    topic: str
    what_went_wrong: str
    correct_answer: str


class SoftSkills(BaseModel):
    clarity: str
    honesty: str
    engagement: str


class FinalFeedback(BaseModel):
    grade: Grade
    hiring_recommendation: HiringRecommendation
    confidence_score: int = Field(ge=0, le=100)

    confirmed_skills: List[str] = []
    knowledge_gaps: List[GapItem] = []

    soft_skills: SoftSkills
    roadmap: List[str] = []
    optional_links: List[str] = []


class InterviewLog(BaseModel):
    participant_name: str
    turns: List[TurnLog] = []
    final_feedback: Optional[FinalFeedback] = None
    meta: Dict[str, Any] = {}
