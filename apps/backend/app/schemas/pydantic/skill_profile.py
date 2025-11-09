from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime


class EvidenceItem(BaseModel):
    """Evidence supporting a detected skill"""
    source: str = Field(..., description="Source of evidence (resume, linkedin, github, etc.)")
    snippet: str = Field(..., description="Text snippet showing skill usage")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score of this evidence")
    offset: Optional[int] = Field(None, description="Character offset in source document")
    href: Optional[str] = Field(None, description="URL to original source (for GitHub commits, LinkedIn posts, etc.)")
    page_number: Optional[int] = Field(None, description="Page number in resume/document")
    line_number: Optional[int] = Field(None, description="Line number in code file")


class SkillItem(BaseModel):
    """A single skill in the user's profile"""
    skill_id: Optional[str] = Field(None, description="Internal ID for this skill instance")
    name: str = Field(..., description="Skill name (e.g., 'Python', 'Machine Learning')")
    category: str = Field(..., description="Skill category (technical, soft, domain, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    evidence: List[EvidenceItem] = Field(default_factory=list, description="Evidence trails supporting this skill")
    mapped_taxonomy_id: Optional[str] = Field(None, description="ESCO or other taxonomy ID")
    manual_status: Literal["suggested", "accepted", "rejected", "edited"] = Field(
        default="suggested",
        description="User interaction status"
    )
    edited_name: Optional[str] = Field(None, description="User-edited skill name if modified")
    tags: List[str] = Field(default_factory=list, description="Additional tags or metadata")


class SkillProfileModel(BaseModel):
    """Complete skill profile for a user"""
    profile_id: str = Field(..., description="Unique profile identifier")
    resume_id: str = Field(..., description="Associated resume ID")
    skills: List[SkillItem] = Field(default_factory=list, description="List of detected and confirmed skills")
    privacy_settings: Dict[str, bool] = Field(
        default_factory=lambda: {"share_github": True, "share_linkedin": True, "mask_pii": True},
        description="Privacy preferences"
    )
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SkillActionRequest(BaseModel):
    """Request to accept, reject, or edit a skill"""
    profile_id: str = Field(..., description="Target profile ID")
    skill_name: str = Field(..., description="Skill to modify")
    action: Literal["accept", "reject", "edit"] = Field(..., description="Action to perform")
    edited_name: Optional[str] = Field(None, description="New name if action is 'edit'")
    edited_category: Optional[str] = Field(None, description="New category if action is 'edit'")


class SkillActionResponse(BaseModel):
    """Response after skill action"""
    success: bool
    message: str
    updated_skill: Optional[SkillItem] = None


class JobMatchRequest(BaseModel):
    """Request to match user skills against a job description"""
    profile_id: str = Field(..., description="User's skill profile ID")
    job_text: str = Field(..., description="Job description text to match against")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of top matches to return")


class MatchedSkill(BaseModel):
    """A skill that matches the job description"""
    name: str
    score: float = Field(..., ge=0.0, le=1.0, description="Match score")
    category: str
    confidence: float


class MissingSkill(BaseModel):
    """A skill required by the job but not in user profile"""
    name: str
    estimated_gap: float = Field(..., ge=0.0, le=1.0, description="How critical this gap is")
    category: str
    from_job_section: Optional[str] = Field(None, description="Which section of JD mentioned this")


class JobMatchResponse(BaseModel):
    """Response from job matching"""
    match_score: float = Field(..., ge=0.0, le=1.0, description="Overall match percentage")
    matched_skills: List[MatchedSkill] = Field(default_factory=list)
    missing_skills: List[MissingSkill] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list, description="Suggested improvements")


class ExportFormat(str):
    """Supported export formats"""
    JSON = "json"
    CSV = "csv"
    SAP = "sap"


class SkillAuditLogModel(BaseModel):
    """Audit log entry"""
    id: int
    profile_id: str
    skill_name: str
    action: str
    previous_value: Optional[Dict]
    new_value: Optional[Dict]
    timestamp: datetime

    class Config:
        from_attributes = True
