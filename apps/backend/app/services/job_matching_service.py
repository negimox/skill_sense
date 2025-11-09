"""Job matching service using embeddings"""
import re
import logging
from typing import List, Tuple
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pydantic.skill_profile import (
    JobMatchRequest,
    JobMatchResponse,
    MatchedSkill,
    MissingSkill,
    SkillItem,
)
from app.agent import EmbeddingManager
from app.skills import get_taxonomy_mapper
from .skill_service import SkillExtractionService

logger = logging.getLogger(__name__)


class JobMatchingService:
    """Service for matching user skills against job descriptions"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_manager = EmbeddingManager()
        self.taxonomy_mapper = get_taxonomy_mapper()
        self.skill_service = SkillExtractionService(db)

    async def match_job(self, request: JobMatchRequest) -> JobMatchResponse:
        """
        Match a user's skill profile against a job description

        Args:
            request: JobMatchRequest with profile_id and job_text

        Returns:
            JobMatchResponse with matched and missing skills
        """
        # Get user's skill profile
        profile = await self.skill_service.get_skill_profile(request.profile_id)
        if not profile:
            return JobMatchResponse(
                match_score=0.0,
                matched_skills=[],
                missing_skills=[],
                recommendations=["Profile not found"]
            )

        # Extract skills from job description
        job_skills = await self._extract_job_skills(request.job_text)

        # Get embeddings for user skills and job skills
        user_skill_embeddings = await self._get_skill_embeddings(
            [skill for skill in profile.skills if skill.manual_status != "rejected"]
        )
        job_skill_embeddings = await self._get_job_skill_embeddings(job_skills)

        # Match skills
        matched_skills, missing_skills = await self._match_skills(
            profile.skills,
            user_skill_embeddings,
            job_skills,
            job_skill_embeddings,
            top_k=request.top_k
        )

        # Calculate overall match score
        match_score = self._calculate_match_score(
            len(matched_skills), len(job_skills)
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            matched_skills, missing_skills
        )

        return JobMatchResponse(
            match_score=match_score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            recommendations=recommendations
        )

    async def _extract_job_skills(self, job_text: str) -> List[Tuple[str, str]]:
        """
        Extract skills mentioned in job description

        Returns:
            List of (skill_name, section) tuples
        """
        skills = []

        # Common skill patterns
        patterns = [
            r'\b(Python|JavaScript|TypeScript|Java|C\+\+|Ruby|Go|Rust|Swift|Kotlin)\b',
            r'\b(React|Angular|Vue\.?js|Next\.?js|Node\.?js|Express|Django|Flask|FastAPI)\b',
            r'\b(AWS|Azure|GCP|Docker|Kubernetes|Jenkins|GitLab|CircleCI)\b',
            r'\b(SQL|PostgreSQL|MySQL|MongoDB|Redis|Elasticsearch)\b',
            r'\b(Machine Learning|Deep Learning|NLP|Computer Vision|Data Science)\b',
            r'\b(TensorFlow|PyTorch|Scikit-learn|Keras|Pandas|NumPy)\b',
            r'\b(Git|Agile|Scrum|DevOps|CI/CD|Microservices|RESTful API)\b',
        ]

        # Try to identify sections
        sections = self._split_into_sections(job_text)

        for section_name, section_text in sections.items():
            for pattern in patterns:
                matches = re.finditer(pattern, section_text, re.IGNORECASE)
                for match in matches:
                    skill_name = match.group(0)
                    skills.append((skill_name, section_name))

        # Deduplicate while preserving order
        seen = set()
        unique_skills = []
        for skill, section in skills:
            skill_lower = skill.lower()
            if skill_lower not in seen:
                seen.add(skill_lower)
                unique_skills.append((skill, section))

        return unique_skills

    def _split_into_sections(self, job_text: str) -> dict:
        """Split job description into sections"""
        sections = {"requirements": "", "responsibilities": "", "qualifications": "", "other": ""}

        # Simple section detection
        text_lower = job_text.lower()

        # Find section boundaries
        req_match = re.search(r'(requirements?|qualifications?|skills?):', text_lower)
        resp_match = re.search(r'(responsibilities?|duties?):', text_lower)

        if req_match:
            start = req_match.start()
            end = resp_match.start() if resp_match and resp_match.start() > start else len(job_text)
            sections["requirements"] = job_text[start:end]

        if resp_match:
            start = resp_match.start()
            end = req_match.start() if req_match and req_match.start() > start else len(job_text)
            sections["responsibilities"] = job_text[start:end]

        if not req_match and not resp_match:
            sections["other"] = job_text

        return sections

    async def _get_skill_embeddings(
        self, skills: List[SkillItem]
    ) -> dict:
        """Get embeddings for user skills"""
        embeddings = {}
        for skill in skills:
            # Use skill name and evidence for richer embedding
            text = f"{skill.name}: {' '.join([e.snippet[:100] for e in skill.evidence[:2]])}"
            try:
                embedding = await self.embedding_manager.embed(text)
                embeddings[skill.name.lower()] = {
                    "embedding": embedding,
                    "skill": skill
                }
            except Exception as e:
                logger.warning(f"Failed to get embedding for skill {skill.name}: {e}")

        return embeddings

    async def _get_job_skill_embeddings(
        self, job_skills: List[Tuple[str, str]]
    ) -> dict:
        """Get embeddings for job skills"""
        embeddings = {}
        for skill_name, section in job_skills:
            try:
                embedding = await self.embedding_manager.embed(skill_name)
                embeddings[skill_name.lower()] = {
                    "embedding": embedding,
                    "section": section
                }
            except Exception as e:
                logger.warning(f"Failed to get embedding for job skill {skill_name}: {e}")

        return embeddings

    async def _match_skills(
        self,
        user_skills: List[SkillItem],
        user_embeddings: dict,
        job_skills: List[Tuple[str, str]],
        job_embeddings: dict,
        top_k: int = 10
    ) -> Tuple[List[MatchedSkill], List[MissingSkill]]:
        """
        Match user skills against job skills using embeddings

        Returns:
            (matched_skills, missing_skills)
        """
        matched_skills = []
        missing_skills = []

        # Track which job skills have been matched
        matched_job_skills = set()

        # For each job skill, find best matching user skill
        for job_skill_name, section in job_skills:
            job_skill_key = job_skill_name.lower()

            if job_skill_key not in job_embeddings:
                continue

            job_embedding = job_embeddings[job_skill_key]["embedding"]
            best_match = None
            best_score = 0.7  # Threshold for considering a match

            # Find best matching user skill
            for user_skill_key, user_data in user_embeddings.items():
                user_embedding = user_data["embedding"]

                # Calculate cosine similarity
                similarity = self._cosine_similarity(user_embedding, job_embedding)

                # Also check exact name match or alias match
                if (user_skill_key == job_skill_key or
                    user_skill_key in job_skill_key or
                    job_skill_key in user_skill_key):
                    similarity = max(similarity, 0.95)

                if similarity > best_score:
                    best_score = similarity
                    best_match = user_data["skill"]

            if best_match:
                matched_skills.append(
                    MatchedSkill(
                        name=job_skill_name,
                        score=round(best_score, 2),
                        category=best_match.category,
                        confidence=best_match.confidence
                    )
                )
                matched_job_skills.add(job_skill_key)
            else:
                # Skill is missing from user profile
                category = self.taxonomy_mapper.get_category(job_skill_name)
                missing_skills.append(
                    MissingSkill(
                        name=job_skill_name,
                        estimated_gap=0.8,  # High gap since it's completely missing
                        category=category,
                        from_job_section=section
                    )
                )

        # Sort matched skills by score
        matched_skills.sort(key=lambda x: x.score, reverse=True)

        # Limit to top_k
        matched_skills = matched_skills[:top_k]

        return matched_skills, missing_skills

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)

            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
        except Exception as e:
            logger.warning(f"Error calculating cosine similarity: {e}")
            return 0.0

    def _calculate_match_score(
        self, matched_count: int, total_job_skills: int
    ) -> float:
        """Calculate overall match percentage"""
        if total_job_skills == 0:
            return 0.0

        score = matched_count / total_job_skills
        return round(score, 2)

    def _generate_recommendations(
        self,
        matched_skills: List[MatchedSkill],
        missing_skills: List[MissingSkill]
    ) -> List[str]:
        """Generate recommendations based on match results"""
        recommendations = []

        if not missing_skills:
            recommendations.append("Great match! You have all the key skills mentioned in the job.")
        elif len(missing_skills) <= 2:
            recommendations.append(
                f"Strong candidate! Consider highlighting: {', '.join([s.name for s in missing_skills])}"
            )
        else:
            # Focus on top missing skills
            top_missing = missing_skills[:3]
            recommendations.append(
                f"Focus on developing: {', '.join([s.name for s in top_missing])}"
            )

        # Analyze categories
        missing_technical = [s for s in missing_skills if s.category == "technical"]
        missing_soft = [s for s in missing_skills if s.category == "soft"]

        if missing_technical:
            recommendations.append(
                f"Consider taking courses in: {', '.join([s.name for s in missing_technical[:2]])}"
            )

        if missing_soft:
            recommendations.append(
                f"Highlight your {', '.join([s.name for s in missing_soft[:2]])} skills in your application"
            )

        return recommendations
