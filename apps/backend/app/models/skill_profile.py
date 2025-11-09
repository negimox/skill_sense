from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, text, Float, Boolean

from .base import Base


class SkillProfile(Base):
    """
    Stores the aggregated skill profile for a user, combining data from
    resume, LinkedIn, GitHub, and other sources.
    """
    __tablename__ = "skill_profiles"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(String, unique=True, nullable=False, index=True)
    resume_id = Column(
        String,
        ForeignKey("processed_resumes.resume_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # JSON array of skill objects
    skills = Column(JSON, nullable=False, default=list)

    # Privacy settings
    privacy_settings = Column(JSON, nullable=True, default=dict)

    created_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    # Relationships
    resume = relationship("ProcessedResume", back_populates="skill_profile")
    audit_logs = relationship("SkillAuditLog", back_populates="profile", cascade="all, delete-orphan")


class SkillAuditLog(Base):
    """
    Tracks all user actions on skills (accept, reject, edit)
    """
    __tablename__ = "skill_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(
        String,
        ForeignKey("skill_profiles.profile_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_name = Column(String, nullable=False)
    action = Column(String, nullable=False)  # "accept", "reject", "edit"
    previous_value = Column(JSON, nullable=True)  # Store previous state for edits
    new_value = Column(JSON, nullable=True)  # Store new state for edits
    timestamp = Column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
        index=True,
    )

    # Relationships
    profile = relationship("SkillProfile", back_populates="audit_logs")
