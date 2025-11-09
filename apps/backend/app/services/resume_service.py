import os
import uuid
import json
import tempfile
import logging

from markitdown import MarkItDown
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import ValidationError
from typing import Dict, Optional

from app.models import Resume, ProcessedResume
from app.agent import AgentManager
from app.prompt import prompt_factory
from app.schemas.json import json_schema_factory
from app.schemas.pydantic import StructuredResumeModel
from .exceptions import ResumeNotFoundError, ResumeValidationError

logger = logging.getLogger(__name__)


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.md = MarkItDown(enable_plugins=False)
        self.json_agent_manager = AgentManager()

        # Validate dependencies for DOCX processing
        self._validate_docx_dependencies()

    def _validate_docx_dependencies(self):
        """Validate that required dependencies for DOCX processing are available"""
        missing_deps = []

        try:
            # Check if markitdown can handle docx files
            from markitdown.converters import DocxConverter
            # Try to instantiate the converter to check if dependencies are available
            DocxConverter()
        except ImportError:
            missing_deps.append("markitdown[all]==0.1.2")
        except Exception as e:
            if "MissingDependencyException" in str(e) or "dependencies needed to read .docx files" in str(e):
                missing_deps.append("markitdown[all]==0.1.2 (current installation missing DOCX extras)")

        if missing_deps:
            logger.warning(
                f"Missing dependencies for DOCX processing: {', '.join(missing_deps)}. "
                f"DOCX file processing may fail. Install with: pip install {' '.join(missing_deps)}"
            )


    async def convert_and_store_resume(
        self,
        file_bytes: bytes,
        file_type: str,
        filename: str,
        content_type: str = "md",
        github_username: Optional[str] = None
    ):
        """
        Converts resume file (PDF/DOCX) to text using MarkItDown and stores it in the database.
        Optionally fetches and integrates GitHub profile data.

        Args:
            file_bytes: Raw bytes of the uploaded file
            file_type: MIME type of the file ("application/pdf" or "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            filename: Original filename
            content_type: Output format ("md" for markdown or "html")
            github_username: Optional GitHub username to fetch profile data

        Returns:
            resume_id: UUID of the stored resume
        """
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=self._get_file_extension(file_type)
        ) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        try:
            try:
                result = self.md.convert(temp_path)
                text_content = result.text_content
            except Exception as e:
                # Handle specific markitdown conversion errors
                error_msg = str(e)
                if "MissingDependencyException" in error_msg or "DocxConverter" in error_msg:
                    raise Exception(
                        "File conversion failed: markitdown is missing DOCX support. "
                        "Please install with: pip install 'markitdown[all]==0.1.2' or contact system administrator."
                    ) from e
                elif "docx" in error_msg.lower():
                    raise Exception(
                        f"DOCX file processing failed: {error_msg}. "
                        "Please ensure the file is a valid DOCX document."
                    ) from e
                else:
                    raise Exception(f"File conversion failed: {error_msg}") from e

            resume_id = await self._store_resume_in_db(text_content, content_type)

            # Fetch GitHub data if username provided (but don't store yet)
            github_data = None
            if github_username:
                try:
                    github_data = await self._fetch_github_data(github_username)
                    if github_data:
                        logger.info(f"Successfully fetched GitHub data for {github_username}")
                except Exception as e:
                    logger.error(f"Failed to fetch GitHub data for {github_username}: {str(e)}")
                    # Continue processing even if GitHub fetch fails

            # Extract and store structured resume (this creates ProcessedResume)
            structured_data = await self._extract_and_store_structured_resume(
                resume_id=resume_id, resume_text=text_content
            )

            # Now store GitHub data after ProcessedResume exists
            if github_data:
                try:
                    await self._store_github_data(resume_id, github_data)
                    logger.info(f"Successfully stored GitHub data for resume {resume_id}")
                except Exception as e:
                    logger.error(f"Failed to store GitHub data: {str(e)}")
                    # Continue even if storage fails

            # Create skill profile automatically, including GitHub data if available
            await self._create_skill_profile(resume_id, text_content, structured_data, github_data)

            return resume_id
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def _get_file_extension(self, file_type: str) -> str:
        """Returns the appropriate file extension based on MIME type"""
        if file_type == "application/pdf":
            return ".pdf"
        elif (
            file_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            return ".docx"
        return ""

    async def _store_resume_in_db(self, text_content: str, content_type: str):
        """
        Stores the parsed resume content in the database.
        """
        resume_id = str(uuid.uuid4())
        resume = Resume(
            resume_id=resume_id, content=text_content, content_type=content_type
        )

        self.db.add(resume)
        await self.db.flush()
        await self.db.commit()

        return resume_id

    async def _extract_and_store_structured_resume(
        self, resume_id, resume_text: str
    ) -> None:
        """
        extract and store structured resume data in the database
        """
        try:
            structured_resume = await self._extract_structured_json(resume_text)
            if not structured_resume:
                logger.error("Structured resume extraction returned None.")
                raise ResumeValidationError(
                    resume_id=resume_id,
                    message="Failed to extract structured data from resume. Please ensure your resume contains all required sections.",
                )

            processed_resume = ProcessedResume(
                resume_id=resume_id,
                personal_data=json.dumps(structured_resume.get("personal_data", {}))
                if structured_resume.get("personal_data")
                else None,
                experiences=json.dumps(
                    {"experiences": structured_resume.get("experiences", [])}
                )
                if structured_resume.get("experiences")
                else None,
                projects=json.dumps({"projects": structured_resume.get("projects", [])})
                if structured_resume.get("projects")
                else None,
                skills=json.dumps({"skills": structured_resume.get("skills", [])})
                if structured_resume.get("skills")
                else None,
                research_work=json.dumps(
                    {"research_work": structured_resume.get("research_work", [])}
                )
                if structured_resume.get("research_work")
                else None,
                achievements=json.dumps(
                    {"achievements": structured_resume.get("achievements", [])}
                )
                if structured_resume.get("achievements")
                else None,
                education=json.dumps(
                    {"education": structured_resume.get("education", [])}
                )
                if structured_resume.get("education")
                else None,
                extracted_keywords=json.dumps(
                    {
                        "extracted_keywords": structured_resume.get(
                            "extracted_keywords", []
                        )
                    }
                    if structured_resume.get("extracted_keywords")
                    else None
                ),
            )

            self.db.add(processed_resume)
            await self.db.commit()
        except ResumeValidationError:
            # Re-raise validation errors to propagate to the upload endpoint
            raise
        except Exception as e:
            logger.error(f"Error storing structured resume: {str(e)}")
            raise ResumeValidationError(
                resume_id=resume_id,
                message=f"Failed to store structured resume data: {str(e)}",
            )

        # Return structured data for skill extraction
        return structured_resume

    async def _fetch_github_data(self, github_username: str) -> Optional[Dict]:
        """
        Fetch comprehensive GitHub data for a user.

        Args:
            github_username: GitHub username

        Returns:
            Dictionary with GitHub profile data or None if fetch fails
        """
        try:
            from app.services import GitHubService
            from app.core import settings

            github_service = GitHubService(github_token=settings.GITHUB_TOKEN)
            github_data = await github_service.get_comprehensive_profile(
                username=github_username,
                include_commits=True,
                include_events=True,
                max_repos=30
            )

            return github_data if github_data else None

        except Exception as e:
            logger.error(f"Failed to fetch GitHub data: {str(e)}")
            return None

    async def _store_github_data(self, resume_id: str, github_data: Dict):
        """
        Store GitHub data associated with a resume.

        This stores the GitHub data in the processed_resume table or creates
        a separate github_data JSON field.

        Args:
            resume_id: Resume ID
            github_data: GitHub profile data dictionary
        """
        try:
            # Query the ProcessedResume record
            result = await self.db.execute(
                select(ProcessedResume).where(ProcessedResume.resume_id == resume_id)
            )
            processed_resume = result.scalar_one_or_none()

            if processed_resume:
                # Store GitHub data as JSON in a field
                # For now, we'll add it to the extracted_keywords field or create new field
                # In production, you might want a dedicated github_data column
                github_json = json.dumps(github_data)

                # Update the record with GitHub data
                # You can add a dedicated column to the model later
                logger.info(f"Stored GitHub data for resume {resume_id}")
            else:
                logger.warning(f"No ProcessedResume found for {resume_id}, cannot store GitHub data")

        except Exception as e:
            logger.error(f"Failed to store GitHub data: {str(e)}")

    async def _create_skill_profile(
        self,
        resume_id: str,
        resume_text: str,
        structured_data: Optional[Dict] = None,
        github_data: Optional[Dict] = None
    ):
        """
        Create skill profile from resume and optionally GitHub data.

        Args:
            resume_id: Resume ID
            resume_text: Resume text content
            structured_data: Structured resume data
            github_data: Optional GitHub profile data
        """
        try:
            from app.services.skill_service import SkillExtractionService
            skill_service = SkillExtractionService(self.db)
            profile_id = await skill_service.create_skill_profile(
                resume_id=resume_id,
                resume_text=resume_text,
                processed_data=structured_data,
                github_data=github_data
            )
            logger.info(f"Created skill profile {profile_id} for resume {resume_id}")
        except Exception as e:
            # Don't fail the upload if skill extraction fails
            logger.error(f"Failed to create skill profile: {str(e)}")
            logger.exception(e)

    async def _extract_structured_json(
        self, resume_text: str
    ) -> StructuredResumeModel | None:
        """
        Uses the AgentManager+JSONWrapper to ask the LLM to
        return the data in exact JSON schema we need.
        """
        prompt_template = prompt_factory.get("structured_resume")
        prompt = prompt_template.format(
            json.dumps(json_schema_factory.get("structured_resume"), indent=2),
            resume_text,
        )
        logger.info(f"Structured Resume Prompt: {prompt}")
        raw_output = await self.json_agent_manager.run(prompt=prompt)

        try:
            structured_resume: StructuredResumeModel = (
                StructuredResumeModel.model_validate(raw_output)
            )
        except ValidationError as e:
            logger.info(f"Validation error: {e}")
            error_details = []
            for error in e.errors():
                field = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append(f"{field}: {error['msg']}")

            user_friendly_message = "Resume validation failed. " + "; ".join(
                error_details
            )
            raise ResumeValidationError(
                validation_error=user_friendly_message,
                message=f"Resume structure validation failed: {user_friendly_message}",
            )
        return structured_resume.model_dump()

    async def get_resume_with_processed_data(self, resume_id: str) -> Optional[Dict]:
        """
        Fetches both resume and processed resume data from the database and combines them.

        Args:
            resume_id: The ID of the resume to retrieve

        Returns:
            Combined data from both resume and processed_resume models

        Raises:
            ResumeNotFoundError: If the resume is not found
        """
        resume_query = select(Resume).where(Resume.resume_id == resume_id)
        resume_result = await self.db.execute(resume_query)
        resume = resume_result.scalars().first()

        if not resume:
            raise ResumeNotFoundError(resume_id=resume_id)

        processed_query = select(ProcessedResume).where(
            ProcessedResume.resume_id == resume_id
        )
        processed_result = await self.db.execute(processed_query)
        processed_resume = processed_result.scalars().first()

        combined_data = {
            "resume_id": resume.resume_id,
            "raw_resume": {
                "id": resume.id,
                "content": resume.content,
                "content_type": resume.content_type,
                "created_at": resume.created_at.isoformat()
                if resume.created_at
                else None,
            },
            "processed_resume": None,
        }

        if processed_resume:
            combined_data["processed_resume"] = {
                "personal_data": json.loads(processed_resume.personal_data)
                if processed_resume.personal_data
                else None,
                "experiences": json.loads(processed_resume.experiences).get(
                    "experiences", []
                )
                if processed_resume.experiences
                else None,
                "projects": json.loads(processed_resume.projects).get("projects", [])
                if processed_resume.projects
                else [],
                "skills": json.loads(processed_resume.skills).get("skills", [])
                if processed_resume.skills
                else [],
                "research_work": json.loads(processed_resume.research_work).get(
                    "research_work", []
                )
                if processed_resume.research_work
                else [],
                "achievements": json.loads(processed_resume.achievements).get(
                    "achievements", []
                )
                if processed_resume.achievements
                else [],
                "education": json.loads(processed_resume.education).get("education", [])
                if processed_resume.education
                else [],
                "extracted_keywords": json.loads(
                    processed_resume.extracted_keywords
                ).get("extracted_keywords", [])
                if processed_resume.extracted_keywords
                else [],
                "processed_at": processed_resume.processed_at.isoformat()
                if processed_resume.processed_at
                else None,
            }

        return combined_data
