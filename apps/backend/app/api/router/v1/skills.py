"""API router for skill profile management"""
import logging
import csv
import io
import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core import get_db_session
from app.services.skill_service import SkillExtractionService
from app.services.job_matching_service import JobMatchingService
from app.schemas.pydantic.skill_profile import (
    SkillProfileModel,
    SkillActionRequest,
    SkillActionResponse,
    JobMatchRequest,
    JobMatchResponse,
    SkillItem,
)

skills_router = APIRouter()
logger = logging.getLogger(__name__)


@skills_router.get(
    "/profile/{profile_id}",
    response_model=SkillProfileModel,
    summary="Get skill profile by ID"
)
async def get_skill_profile(
    profile_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieve a skill profile by its ID

    Args:
        profile_id: Unique profile identifier

    Returns:
        SkillProfileModel with all skills and evidence
    """
    service = SkillExtractionService(db)
    profile = await service.get_skill_profile(profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )

    return profile


@skills_router.get(
    "/profile/by-resume/{resume_id}",
    response_model=SkillProfileModel,
    summary="Get skill profile by resume ID"
)
async def get_profile_by_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieve a skill profile by resume ID

    Args:
        resume_id: Resume identifier

    Returns:
        SkillProfileModel associated with the resume
    """
    service = SkillExtractionService(db)
    profile = await service.get_profile_by_resume_id(resume_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No profile found for resume {resume_id}"
        )

    return profile


@skills_router.post(
    "/skill/action",
    response_model=SkillActionResponse,
    summary="Accept, reject, or edit a skill"
)
async def skill_action(
    request: SkillActionRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Handle user action on a skill (accept, reject, edit)

    Args:
        request: SkillActionRequest with profile_id, skill_name, action

    Returns:
        SkillActionResponse with success status and updated skill
    """
    service = SkillExtractionService(db)
    success, message, updated_skill = await service.update_skill_action(request)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return SkillActionResponse(
        success=success,
        message=message,
        updated_skill=updated_skill
    )


@skills_router.post(
    "/match-job",
    response_model=JobMatchResponse,
    summary="Match user skills against a job description"
)
async def match_job(
    request: JobMatchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Compare user skill profile against a job description

    Args:
        request: JobMatchRequest with profile_id and job_text

    Returns:
        JobMatchResponse with match score, matched skills, and missing skills
    """
    service = JobMatchingService(db)
    result = await service.match_job(request)

    return result


@skills_router.get(
    "/export/{profile_id}",
    summary="Export skill profile in various formats"
)
async def export_profile(
    profile_id: str,
    format: str = Query("json", regex="^(json|csv|sap)$"),
    mask_pii: bool = Query(True, description="Whether to mask PII in export"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Export skill profile in JSON, CSV, or SAP format

    Args:
        profile_id: Profile to export
        format: Export format (json, csv, sap)
        mask_pii: Whether to mask personally identifiable information

    Returns:
        File download with the exported data
    """
    service = SkillExtractionService(db)
    profile = await service.get_skill_profile(profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile {profile_id} not found"
        )

    # Apply PII masking if requested
    if mask_pii:
        profile = _mask_pii_in_profile(profile)

    # Generate export based on format
    if format == "json":
        return _export_as_json(profile)
    elif format == "csv":
        return _export_as_csv(profile)
    elif format == "sap":
        return _export_as_sap(profile)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format: {format}"
        )


def _mask_pii_in_profile(profile: SkillProfileModel) -> SkillProfileModel:
    """Mask PII (emails, phone numbers) in profile evidence"""
    import re

    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # Phone pattern (simple)
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'

    for skill in profile.skills:
        for evidence in skill.evidence:
            # Mask emails
            evidence.snippet = re.sub(email_pattern, '[EMAIL]', evidence.snippet)
            # Mask phones
            evidence.snippet = re.sub(phone_pattern, '[PHONE]', evidence.snippet)

    return profile


def _export_as_json(profile: SkillProfileModel) -> JSONResponse:
    """Export profile as JSON"""
    data = profile.model_dump(mode='json')

    return JSONResponse(
        content=data,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=skill_profile_{profile.profile_id}.json"
        }
    )


def _export_as_csv(profile: SkillProfileModel) -> StreamingResponse:
    """Export profile as CSV"""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Skill Name", "Category", "Confidence", "Status",
        "ESCO ID", "Evidence Count", "Sources"
    ])

    # Rows
    for skill in profile.skills:
        # Only export accepted or suggested skills
        if skill.manual_status != "rejected":
            sources = ", ".join(set(e.source for e in skill.evidence))
            writer.writerow([
                skill.edited_name or skill.name,
                skill.category,
                skill.confidence,
                skill.manual_status,
                skill.mapped_taxonomy_id or "",
                len(skill.evidence),
                sources
            ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=skills_{profile.profile_id}.csv"
        }
    )


def _export_as_sap(profile: SkillProfileModel) -> StreamingResponse:
    """
    Export profile in SAP SuccessFactors Job Profile Builder format

    Based on SAP SuccessFactors documentation:
    https://help.sap.com/docs/successfactors-platform/implementing-and-managing-job-profile-builder/
    importing-new-job-profile-content-using-manage-job-profile-content-import-export-option

    This format includes:
    - External Code (ESCO URI or custom ID)
    - Name (skill name)
    - Proficiency Rating (1-5 scale)
    - Proficiency Level Name (text description)
    - Skill Type (technical/soft/domain)
    - Last Modified Date
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # SAP SuccessFactors format header
    writer.writerow([
        "externalCode",
        "name_en_US",
        "proServRatingScaleOption",
        "proServRatingScaleLabel",
        "libraryId",
        "category",
        "lastModifiedDateTime",
        "status"
    ])

    # Proficiency level mapping based on confidence
    def get_proficiency_details(confidence: float):
        """Map confidence score to SAP proficiency levels"""
        if confidence >= 0.9:
            return ("5", "Expert")
        elif confidence >= 0.75:
            return ("4", "Advanced")
        elif confidence >= 0.6:
            return ("3", "Intermediate")
        elif confidence >= 0.4:
            return ("2", "Basic")
        else:
            return ("1", "Novice")

    # Rows - export accepted and suggested skills (for SAP import flexibility)
    for skill in profile.skills:
        if skill.manual_status in ["accepted", "suggested"]:
            # Use ESCO URI if available, otherwise create custom ID
            external_code = skill.mapped_taxonomy_id or f"CUSTOM_{skill.name.upper().replace(' ', '_')}"

            # Map confidence to proficiency
            proficiency_num, proficiency_label = get_proficiency_details(skill.confidence)

            # Determine library ID (ESCO for mapped skills, CUSTOM for others)
            library_id = "ESCO" if skill.mapped_taxonomy_id else "CUSTOM"

            # Status based on manual_status
            status = "ACTIVE" if skill.manual_status == "accepted" else "SUGGESTED"

            writer.writerow([
                external_code,
                skill.edited_name or skill.name,
                proficiency_num,
                proficiency_label,
                library_id,
                skill.category.upper(),
                profile.updated_at.strftime("%Y-%m-%dT%H:%M:%S"),
                status
            ])

    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=sap_successfactors_skills_{profile.profile_id}.csv"
        }
    )
