"""Skill extraction and profile management service"""
import uuid
import logging
import re
from dataclasses import dataclass
from collections import defaultdict
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update

from app.models import SkillProfile, SkillAuditLog
from app.schemas.pydantic.skill_profile import (
    SkillItem,
    EvidenceItem,
    SkillProfileModel,
    SkillActionRequest,
)
from app.agent import EmbeddingManager
from app.skills import get_taxonomy_mapper
from .exceptions import ResumeNotFoundError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkillEntry:
    canonical_name: str
    alias: str
    normalized: str
    tokens: Tuple[str, ...]
    esco_id: Optional[str]
    category: str
    skill_type: Optional[str]
    requires_context: bool


@dataclass(frozen=True)
class SkillMatch:
    entry: SkillEntry
    start: int
    end: int
    matched_text: str
    snippet: str


class SkillMatcher:
    """Efficient matcher leveraging the ESCO taxonomy"""

    TOKEN_PATTERN = re.compile(r"[a-z0-9\+\#\.]+")
    SHORT_TOKEN_WHITELIST = {
        "sql", "aws", "git", "css", "html", "ux", "ui", "qa",
        "bi", "sap", "sas", "etl", "crm"
    }
    GENERIC_SINGLE_TOKENS = {
        "excel", "word", "office", "drive", "access", "outlook", "teams"
    }
    STRICT_CONTEXT_TERMS: Dict[str, Dict[str, object]] = {
        "excel": {"keywords": ("microsoft", "ms office", "spreadsheet"), "allow_list": True},
        "word": {"keywords": ("microsoft", "ms office", "document"), "allow_list": True},
        "office": {"keywords": ("microsoft", "ms office", "suite"), "allow_list": True},
        "drive": {"keywords": ("google", "g suite", "workspace"), "allow_list": True},
        "access": {"keywords": ("microsoft", "database"), "allow_list": True},
        "outlook": {"keywords": ("microsoft", "ms"), "allow_list": True},
        "teams": {"keywords": ("microsoft", "ms"), "allow_list": True},
        "google": {"keywords": ("search", "engine", "seo", "ads", "results", "query"), "allow_list": False},
        "yahoo": {"keywords": ("search", "engine", "seo"), "allow_list": False},
        "logic": {"keywords": ("formal logic", "logical", "boolean", "symbolic", "circuit", "predicate"), "allow_list": False},
        "report": {"keywords": ("facts", "write", "writing", "prepare", "draft", "document", "statement"), "allow_list": False},
        "source": {"keywords": ("game", "engine", "valve", "hammer", "sdk"), "allow_list": False},
    }
    GENERAL_CONTEXT_KEYWORDS = (
        "experience", "experiences", "skill", "skills", "skilled",
        "proficient", "proficiency", "knowledge", "familiar", "familiarity",
        "using", "use", "utilized", "utilised", "expertise", "certified",
        "tools", "technologies", "technology", "framework", "frameworks",
        "stack", "worked", "hands-on", "hands on", "background", "projects",
        "responsible for", "competency", "competencies"
    )
    LIST_SYMBOLS = ("•", "·", "-", "*")
    NEGATIVE_CONTEXT_PATTERNS = {
        "excel": re.compile(r"\\bexcel(?:led|s|ing)?\\s+(?:at|in)\\b")
    }

    _cache: Optional[Dict[str, object]] = None
    _shared_instance: Optional["SkillMatcher"] = None

    def __init__(self, taxonomy_mapper, excluded: Optional[Set[str]] = None):
        self.taxonomy_mapper = taxonomy_mapper
        self.excluded = {s.lower() for s in (excluded or set())}

        if SkillMatcher._cache is None:
            SkillMatcher._cache = self._build_index(taxonomy_mapper)

        cache = SkillMatcher._cache
        self.index: Dict[str, List[SkillEntry]] = cache["index"]
        self.normalized_lookup: Dict[str, SkillEntry] = cache["normalized_lookup"]
        self.max_tokens: int = cache["max_tokens"]

    @classmethod
    def shared(cls, taxonomy_mapper, excluded: Optional[Set[str]] = None) -> "SkillMatcher":
        if cls._shared_instance is None:
            cls._shared_instance = cls(taxonomy_mapper, excluded)
        else:
            if excluded:
                cls._shared_instance.excluded.update(s.lower() for s in excluded)
        return cls._shared_instance

    @classmethod
    def _build_index(cls, taxonomy_mapper) -> Dict[str, object]:
        index: Dict[str, List[SkillEntry]] = defaultdict(list)
        normalized_lookup: Dict[str, SkillEntry] = {}
        unique_entries: Dict[Tuple[str, str], SkillEntry] = {}
        max_tokens = 0

        for mapping in taxonomy_mapper.get_all_mappings():
            canonical = mapping.get("skill_name")
            if not canonical:
                continue

            aliases = [canonical] + mapping.get("aliases", [])
            esco_id = mapping.get("esco_id")
            category = mapping.get("category", "technical")
            skill_type = mapping.get("skill_type")

            for phrase in aliases:
                for tokens in cls._generate_token_variants(phrase):
                    normalized = " ".join(tokens)
                    if not normalized:
                        continue

                    key = (canonical.lower(), normalized)
                    entry = unique_entries.get(key)
                    if entry is None:
                        requires_context = cls._should_require_context(tokens)
                        entry = SkillEntry(
                            canonical_name=canonical,
                            alias=phrase,
                            normalized=normalized,
                            tokens=tokens,
                            esco_id=esco_id,
                            category=category,
                            skill_type=skill_type,
                            requires_context=requires_context
                        )
                        unique_entries[key] = entry
                        max_tokens = max(max_tokens, len(tokens))

                    normalized_lookup.setdefault(normalized, entry)
                    index[tokens[0]].append(entry)

        return {
            "index": {token: entries for token, entries in index.items()},
            "normalized_lookup": normalized_lookup,
            "max_tokens": max_tokens,
        }

    @classmethod
    def _generate_token_variants(cls, phrase: str) -> Set[Tuple[str, ...]]:
        if not phrase:
            return set()

        lower = phrase.lower()
        variants = {lower}
        replacements = [
            ("/", " "),
            ("-", " "),
            ("_", " "),
            ("&", " and "),
            ("+", " plus "),
        ]

        for char, replacement in replacements:
            updated = set()
            for variant in variants:
                if char in variant:
                    updated.add(variant.replace(char, replacement))
            variants.update(updated)

        dotted_variants = set()
        for variant in variants:
            dotted_variants.add(variant)
            if "." in variant:
                dotted_variants.add(variant.replace(".", " "))

        token_sets: Set[Tuple[str, ...]] = set()
        for variant in dotted_variants:
            tokens = tuple(filter(None, cls.TOKEN_PATTERN.findall(variant)))
            if tokens:
                token_sets.add(tokens)

        return token_sets

    @classmethod
    def _should_require_context(cls, tokens: Tuple[str, ...]) -> bool:
        if len(tokens) > 1:
            return False

        token = tokens[0]
        if token in cls.SHORT_TOKEN_WHITELIST:
            return False

        if len(token) <= 2:
            return True

        if token in cls.STRICT_CONTEXT_TERMS:
            return True

        return token in cls.GENERIC_SINGLE_TOKENS

    @staticmethod
    def _extract_context(text: str, start: int, end: int, radius: int = 60) -> str:
        snippet_start = max(0, start - radius)
        snippet_end = min(len(text), end + radius)
        return text[snippet_start:snippet_end]

    @classmethod
    def _is_list_context(cls, snippet: str, snippet_lower: str) -> bool:
        stripped = snippet.strip()
        if stripped.startswith(cls.LIST_SYMBOLS):
            return True

        if any(symbol in snippet for symbol in cls.LIST_SYMBOLS):
            return True

        return bool(re.search(r"\b(skills?|tools?|technologies?|stack):", snippet_lower))

    @classmethod
    def _has_positive_context(cls, snippet: str, snippet_lower: str) -> bool:
        if any(keyword in snippet_lower for keyword in cls.GENERAL_CONTEXT_KEYWORDS):
            return True

        return cls._is_list_context(snippet, snippet_lower)

    def context_is_valid(self, entry: SkillEntry, snippet: str) -> bool:
        snippet_lower = snippet.lower()

        if entry.requires_context:
            token = entry.tokens[0]
            strict_config = self.STRICT_CONTEXT_TERMS.get(token)

            if strict_config:
                keywords = strict_config.get("keywords", ())
                allow_list = strict_config.get("allow_list", False)
                has_keyword = any(term in snippet_lower for term in keywords)

                if not has_keyword:
                    if not allow_list:
                        return False
                    if not self._is_list_context(snippet, snippet_lower):
                        return False

                negative = self.NEGATIVE_CONTEXT_PATTERNS.get(token)
                if negative and negative.search(snippet_lower):
                    return False
            elif not self._has_positive_context(snippet, snippet_lower):
                return False

        return True

    @staticmethod
    def _spans_overlap(first: SkillMatch, second: SkillMatch) -> bool:
        return not (first.end <= second.start or first.start >= second.end)

    def match(self, text: str) -> List[SkillMatch]:
        if not text:
            return []

        text_lower = text.lower()
        token_matches = list(self.TOKEN_PATTERN.finditer(text_lower))
        if not token_matches:
            return []

        raw_matches: List[SkillMatch] = []
        seen_spans: Set[Tuple[str, int, int]] = set()
        total_tokens = len(token_matches)

        for idx, token_match in enumerate(token_matches):
            token = token_match.group(0)
            candidates = self.index.get(token)
            if not candidates:
                continue

            for entry in candidates:
                length = len(entry.tokens)
                if idx + length > total_tokens:
                    continue

                window = token_matches[idx:idx + length]
                candidate_tokens = [m.group(0) for m in window]
                normalized_candidate = " ".join(candidate_tokens)

                if normalized_candidate != entry.normalized:
                    continue

                start = window[0].start()
                end = window[-1].end()

                canonical_lower = entry.canonical_name.lower()
                if canonical_lower in self.excluded or entry.normalized in self.excluded:
                    continue

                span_key = (canonical_lower, start, end)
                if span_key in seen_spans:
                    continue

                snippet = self._extract_context(text, start, end)
                if not self.context_is_valid(entry, snippet):
                    continue

                raw_matches.append(
                    SkillMatch(
                        entry=entry,
                        start=start,
                        end=end,
                        matched_text=text[start:end],
                        snippet=snippet
                    )
                )
                seen_spans.add(span_key)

        if not raw_matches:
            return []

        raw_matches.sort(key=lambda m: (len(m.entry.tokens), m.end - m.start), reverse=True)

        filtered: List[SkillMatch] = []
        for match in raw_matches:
            if any(self._spans_overlap(match, existing) for existing in filtered):
                continue
            filtered.append(match)

        filtered.sort(key=lambda m: m.start)
        return filtered

    def resolve_phrase(self, phrase: str) -> Optional[SkillEntry]:
        if not phrase:
            return None

        for tokens in self._generate_token_variants(phrase):
            normalized = " ".join(tokens)
            entry = self.normalized_lookup.get(normalized)
            if entry and entry.canonical_name.lower() not in self.excluded:
                return entry

        return None

    def has_positive_context(self, snippet: str) -> bool:
        snippet_lower = snippet.lower()
        return self._has_positive_context(snippet, snippet_lower)

class SkillExtractionService:
    """Service for extracting skills from resumes and managing skill profiles"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedding_manager = EmbeddingManager()
        self.taxonomy_mapper = get_taxonomy_mapper()
        self.excluded_skills = {
            "r",
            "code",
        }

        self.skill_matcher = SkillMatcher.shared(self.taxonomy_mapper, self.excluded_skills)
        self.minimum_confidence = 0.55
        self.structured_label_stopwords = {
            "skills",
            "technical skills",
            "programming skills",
            "soft skills",
            "programming languages",
            "languages",
            "professional skills",
            "tools",
            "tooling",
            "frameworks",
            "competencies",
            "certifications",
            "summary",
            "professional summary",
            "profile",
            "experience",
            "work experience",
            "projects",
        }

    async def create_skill_profile(
        self,
        resume_id: str,
        resume_text: str,
        processed_data: Optional[Dict] = None,
        github_data: Optional[Dict] = None
    ) -> str:
        """
        Create a skill profile from a resume and optionally GitHub data

        Args:
            resume_id: ID of the processed resume
            resume_text: Raw resume text
            processed_data: Optional pre-processed resume data
            github_data: Optional GitHub profile data

        Returns:
            profile_id: ID of the created skill profile
        """
        # Check if profile already exists
        existing = await self.db.execute(
            select(SkillProfile).where(SkillProfile.resume_id == resume_id)
        )
        existing_profile = existing.scalar_one_or_none()

        if existing_profile:
            logger.info(f"Skill profile already exists for resume {resume_id}")
            return existing_profile.profile_id

        # Extract skills from resume
        skills = await self._extract_skills(resume_text, processed_data)

        # Enhance skills with GitHub data if available
        if github_data:
            try:
                github_skills = await self._extract_github_skills(github_data)
                # Merge GitHub skills with resume skills
                skills = self._merge_skills(skills, github_skills)
                logger.info(f"Enhanced profile with {len(github_skills)} skills from GitHub")
            except Exception as e:
                logger.error(f"Failed to extract GitHub skills: {str(e)}")

        # Create profile
        profile_id = str(uuid.uuid4())
        profile = SkillProfile(
            profile_id=profile_id,
            resume_id=resume_id,
            skills=[skill.model_dump() for skill in skills],
            privacy_settings={"share_github": True, "share_linkedin": True, "mask_pii": True}
        )

        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)

        logger.info(f"Created skill profile {profile_id} with {len(skills)} skills")
        return profile_id

    async def _extract_skills(
        self, resume_text: str, processed_data: Optional[Dict] = None
    ) -> List[SkillItem]:
        """
        Extract skills from resume text and optional structured data

        Args:
            resume_text: Raw resume text
            processed_data: Optional structured resume data

        Returns:
            List of SkillItem objects
        """
        skills_dict: Dict[str, Dict] = {}

        matches = self.skill_matcher.match(resume_text)
        for match in matches:
            self._add_or_update_skill(
                skills_dict=skills_dict,
                skill_name=match.entry.canonical_name,
                full_text=resume_text,
                start=match.start,
                end=match.end,
                source="resume",
                skill_entry=match.entry,
                matched_text=match.matched_text,
                snippet_override=match.snippet,
                validate=True,
            )

        if processed_data:
            for skill in self._iter_skill_strings(processed_data.get("skills")):
                entry = self.skill_matcher.resolve_phrase(skill)
                if not entry:
                    continue
                self._add_or_update_skill(
                    skills_dict=skills_dict,
                    skill_name=entry.canonical_name,
                    full_text=resume_text,
                    start=0,
                    end=0,
                    source="structured",
                    skill_entry=entry,
                    matched_text=skill,
                    snippet_override=skill,
                    validate=False,
                )

        skills_list: List[SkillItem] = []
        for skill_key, skill_data in skills_dict.items():
            confidence = self._calculate_confidence(skill_data["evidence"])
            if confidence < self.minimum_confidence:
                continue

            mapping = self.taxonomy_mapper.get_mapping(skill_data["name"]) or self.taxonomy_mapper.get_mapping(skill_key)
            mapped_id = mapping.get("esco_id") if mapping else None
            category = mapping.get("category") if mapping else skill_data.get("category") or "technical"
            canonical_name = mapping.get("skill_name") if mapping else skill_data["name"]
            tags = sorted(skill_data.get("matched_terms", []))

            skills_list.append(
                SkillItem(
                    skill_id=str(uuid.uuid4()),
                    name=canonical_name,
                    category=category,
                    confidence=confidence,
                    evidence=skill_data["evidence"],
                    mapped_taxonomy_id=mapped_id,
                    manual_status="suggested",
                    tags=tags,
                )
            )

        skills_list.sort(key=lambda x: x.confidence, reverse=True)
        return skills_list

    async def _extract_github_skills(self, github_data: Dict) -> List[SkillItem]:
        """
        Extract skills from GitHub data

        Args:
            github_data: GitHub comprehensive profile data

        Returns:
            List of SkillItem objects extracted from GitHub
        """
        from app.services import GitHubService

        skills_dict: Dict[str, Dict] = {}

        # Extract skills using the GitHub service's extractor
        github_service = GitHubService()
        extracted = github_service.extract_skills_from_github(github_data)

        if not extracted:
            return []

        # Process programming languages
        for lang_data in extracted.get("programming_languages", []):
            language = lang_data.get("language")
            proficiency = lang_data.get("proficiency", "Intermediate")
            percentage = lang_data.get("percentage", 0)

            evidence = {
                "source": "github",
                "text": f"GitHub: {percentage:.1f}% of code, {proficiency} proficiency",
                "href": extracted.get("github_url")
            }

            skill_key = language.lower()
            if skill_key not in skills_dict:
                skills_dict[skill_key] = {
                    "name": language,
                    "evidence": [evidence],
                    "category": "technical"
                }
            else:
                skills_dict[skill_key]["evidence"].append(evidence)

        # Process technologies
        for tech in extracted.get("technologies", []):
            evidence = {
                "source": "github",
                "text": f"Used in GitHub projects",
                "href": extracted.get("github_url")
            }

            skill_key = tech.lower()
            if skill_key not in skills_dict:
                skills_dict[skill_key] = {
                    "name": tech,
                    "evidence": [evidence],
                    "category": "technical"
                }
            else:
                skills_dict[skill_key]["evidence"].append(evidence)

        # Process project highlights for skills
        for project in extracted.get("project_highlights", [])[:5]:  # Top 5 projects
            if project.get("language"):
                language = project["language"]
                evidence = {
                    "source": "github",
                    "text": f"Project: {project['name']} ({project.get('stars', 0)} stars)",
                    "href": project.get("url")
                }

                skill_key = language.lower()
                if skill_key not in skills_dict:
                    skills_dict[skill_key] = {
                        "name": language,
                        "evidence": [evidence],
                        "category": "technical"
                    }
                else:
                    skills_dict[skill_key]["evidence"].append(evidence)

        # Convert to SkillItem objects
        skills_list = []
        for skill_key, skill_data in skills_dict.items():
            confidence = self._calculate_confidence(skill_data["evidence"])

            mapping = self.taxonomy_mapper.get_mapping(skill_data["name"]) or self.taxonomy_mapper.get_mapping(skill_key)
            mapped_id = mapping.get("esco_id") if mapping else None
            category = mapping.get("category") if mapping else skill_data.get("category") or "technical"
            canonical_name = mapping.get("skill_name") if mapping else skill_data["name"]

            skills_list.append(
                SkillItem(
                    skill_id=str(uuid.uuid4()),
                    name=canonical_name,
                    category=category,
                    confidence=confidence,
                    evidence=skill_data["evidence"],
                    mapped_taxonomy_id=mapped_id,
                    manual_status="suggested",
                    tags=[],
                )
            )

        return skills_list

    def _merge_skills(self, resume_skills: List[SkillItem], github_skills: List[SkillItem]) -> List[SkillItem]:
        """
        Merge skills from resume and GitHub, avoiding duplicates

        Args:
            resume_skills: Skills extracted from resume
            github_skills: Skills extracted from GitHub

        Returns:
            Merged list of unique skills
        """
        skills_dict: Dict[str, SkillItem] = {}

        # Add all resume skills first
        for skill in resume_skills:
            key = skill.name.lower()
            skills_dict[key] = skill

        # Merge GitHub skills
        for github_skill in github_skills:
            key = github_skill.name.lower()

            if key in skills_dict:
                # Skill exists, merge evidence
                existing_skill = skills_dict[key]
                merged_evidence = list(existing_skill.evidence) + list(github_skill.evidence)

                # Create updated skill with merged evidence
                skills_dict[key] = SkillItem(
                    skill_id=existing_skill.skill_id,
                    name=existing_skill.name,
                    category=existing_skill.category,
                    confidence=max(existing_skill.confidence, github_skill.confidence),
                    evidence=merged_evidence,
                    mapped_taxonomy_id=existing_skill.mapped_taxonomy_id or github_skill.mapped_taxonomy_id,
                    manual_status=existing_skill.manual_status,
                    tags=list(set(existing_skill.tags + github_skill.tags)),
                )
            else:
                # New skill from GitHub
                skills_dict[key] = github_skill

        return list(skills_dict.values())

    def _iter_skill_strings(self, data) -> List[str]:
        if not data:
            return []

        skills: List[str] = []

        if isinstance(data, str):
            value = data.strip()
            if value and value.lower() not in self.structured_label_stopwords:
                skills.append(value)
        elif isinstance(data, list):
            for item in data:
                skills.extend(self._iter_skill_strings(item))
        elif isinstance(data, dict):
            for value in data.values():
                skills.extend(self._iter_skill_strings(value))

        # Preserve order while removing duplicates
        seen: Set[str] = set()
        deduped: List[str] = []
        for skill in skills:
            if skill not in seen:
                seen.add(skill)
                deduped.append(skill)

        return deduped

    def _add_or_update_skill(
        self,
        skills_dict: Dict,
        skill_name: str,
        full_text: str,
        start: int,
        end: int,
        source: str,
        skill_entry: Optional[SkillEntry] = None,
        matched_text: Optional[str] = None,
        snippet_override: Optional[str] = None,
        validate: bool = True,
    ):
        """Add or update a skill in the skills dictionary"""
        canonical_name = (skill_entry.canonical_name if skill_entry else skill_name).strip()
        if not canonical_name:
            return

        skill_key = canonical_name.lower()
        if skill_key in self.excluded_skills:
            return

        target_text = (matched_text or canonical_name).strip()

        if validate and not self._validate_skill_match(
            full_text,
            start,
            end,
            target_text,
            skill_entry=skill_entry,
            matched_text=matched_text,
        ):
            return

        snippet = snippet_override if snippet_override is not None else full_text[
            max(0, start - 60): min(len(full_text), end + 60)
        ].strip()

        if not snippet:
            snippet = target_text

        if source == "resume" and skill_entry and not self.skill_matcher.context_is_valid(skill_entry, snippet):
            return

        score = self._score_evidence(snippet, canonical_name, source, skill_entry)

        evidence = EvidenceItem(
            source=source,
            snippet=snippet,
            score=score,
            offset=start if validate else None
        )

        entry = skills_dict.get(skill_key)
        if not entry:
            entry = {
                "name": canonical_name,
                "evidence": [],
                "matched_terms": set(),
                "category": skill_entry.category if skill_entry else None,
            }
            skills_dict[skill_key] = entry

        existing_snippets = {e.snippet for e in entry["evidence"]}
        if snippet not in existing_snippets:
            entry["evidence"].append(evidence)

        entry["matched_terms"].add(target_text)

        if skill_entry and not entry.get("category"):
            entry["category"] = skill_entry.category

    def _validate_skill_match(
        self,
        text: str,
        start: int,
        end: int,
        skill_name: str,
        skill_entry: Optional[SkillEntry] = None,
        matched_text: Optional[str] = None,
    ) -> bool:
        """
        Validate that a regex match is a genuine skill, not a partial match

        Returns False if:
        - The match is part of a URL/email
        - The match is inside another word (e.g., "ML" in "MATLAB")
        - The match lacks proper context
        """
        if not skill_name:
            return False

        if start < 0 or end > len(text):
            return False

        context_start = max(0, start - 24)
        context_end = min(len(text), end + 24)
        context = text[context_start:context_end]

        if re.search(r'[a-z0-9-]+\.(com|io|org|net|dev|app)', context, re.IGNORECASE):
            return False

        if re.search(r'[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}', context, re.IGNORECASE):
            return False

        target = (matched_text or skill_name).strip()
        if not target:
            return False

        if len(target) <= 3:
            if start > 0 and text[start - 1].isalpha():
                return False
            if end < len(text) and text[end].isalpha():
                return False

        return True

    def _score_evidence(
        self,
        snippet: str,
        skill_name: str,
        source: str,
        skill_entry: Optional[SkillEntry] = None
    ) -> float:
        """
        Score how relevant a snippet is as evidence for a skill

        Returns score between 0.0 and 1.0
        """
        snippet_lower = snippet.lower()
        target_lower = skill_name.lower()

        score = 0.85 if source == "structured" else 0.45

        if source == "resume" and self.skill_matcher.has_positive_context(snippet):
            score += 0.2

        year_patterns = [
            r'\d+\+?\s*years?',
            r'years?\s+of\s+experience',
            r'\d+\+?\s*yrs?'
        ]
        for pattern in year_patterns:
            if re.search(pattern, snippet_lower) and target_lower in snippet_lower:
                score += 0.2
                break

        strong_contexts = [
            "experience with", "experience in", "proficient in", "expert in", "skilled in",
            "worked with", "developed using", "built with", "implemented", "implementing",
            "specialized in", "knowledge of", "familiar with", "strong knowledge",
            "hands-on experience", "extensive experience", "programming languages:",
            "technologies:", "skills:", "technical skills:"
        ]
        for context in strong_contexts:
            if context in snippet_lower:
                score += 0.2
                break

        achievement_words = [
            "project", "developed", "built", "created", "designed",
            "architected", "implemented", "delivered", "launched"
        ]
        if any(word in snippet_lower for word in achievement_words):
            score += 0.12

        if any(indicator in snippet for indicator in ("•", "·", ";", " - ", ", ")):
            score += 0.1

        weak_contexts = ["including", "such as", "like", "etc"]
        if any(context in snippet_lower for context in weak_contexts):
            score -= 0.05

        if skill_entry and skill_entry.requires_context and source == "resume":
            score += 0.05

        return min(1.0, max(0.0, score))

    def _calculate_confidence(self, evidence: List[EvidenceItem]) -> float:
        """
        Calculate overall confidence score for a skill based on evidence

        Factors:
        - Number of evidence items (frequency)
        - Quality of evidence (scores)
        - Diversity of sources
        """
        if not evidence:
            return 0.0

        freq_score = min(1.0, 0.4 + (len(evidence) - 1) * 0.2)

        quality_scores = [e.score for e in evidence if e.score is not None]
        if not quality_scores:
            return 0.0

        max_quality = max(quality_scores)
        avg_quality = sum(quality_scores) / len(quality_scores)
        combined_quality = 0.65 * max_quality + 0.35 * avg_quality

        sources = {e.source for e in evidence if e.source}
        diversity_score = min(1.0, len(sources) / 3.0) if sources else 0.0

        confidence = (
            0.2 * freq_score +
            0.7 * combined_quality +
            0.1 * diversity_score
        )

        return round(min(1.0, max(0.0, confidence)), 2)

    async def get_skill_profile(self, profile_id: str) -> Optional[SkillProfileModel]:
        """Get a skill profile by ID"""
        result = await self.db.execute(
            select(SkillProfile).where(SkillProfile.profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        return SkillProfileModel(
            profile_id=profile.profile_id,
            resume_id=profile.resume_id,
            skills=[SkillItem(**skill) for skill in profile.skills],
            privacy_settings=profile.privacy_settings or {},
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    async def get_profile_by_resume_id(self, resume_id: str) -> Optional[SkillProfileModel]:
        """Get a skill profile by resume ID"""
        result = await self.db.execute(
            select(SkillProfile).where(SkillProfile.resume_id == resume_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return None

        return SkillProfileModel(
            profile_id=profile.profile_id,
            resume_id=profile.resume_id,
            skills=[SkillItem(**skill) for skill in profile.skills],
            privacy_settings=profile.privacy_settings or {},
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )

    async def update_skill_action(
        self, request: SkillActionRequest
    ) -> Tuple[bool, str, Optional[SkillItem]]:
        """
        Handle user action on a skill (accept, reject, edit)

        Returns:
            (success, message, updated_skill)
        """
        # Get profile
        result = await self.db.execute(
            select(SkillProfile).where(SkillProfile.profile_id == request.profile_id)
        )
        profile = result.scalar_one_or_none()

        if not profile:
            return False, "Profile not found", None

        # Find the skill
        skills = profile.skills
        skill_index = None
        for i, skill in enumerate(skills):
            if skill["name"].lower() == request.skill_name.lower():
                skill_index = i
                break

        if skill_index is None:
            return False, f"Skill '{request.skill_name}' not found in profile", None

        # Store previous state for audit
        previous_state = skills[skill_index].copy()

        # Apply action
        if request.action == "accept":
            skills[skill_index]["manual_status"] = "accepted"
            message = f"Skill '{request.skill_name}' accepted"

        elif request.action == "reject":
            skills[skill_index]["manual_status"] = "rejected"
            message = f"Skill '{request.skill_name}' rejected"

        elif request.action == "edit":
            skills[skill_index]["manual_status"] = "edited"
            if request.edited_name:
                skills[skill_index]["edited_name"] = request.edited_name
            if request.edited_category:
                skills[skill_index]["category"] = request.edited_category
            message = f"Skill '{request.skill_name}' edited"

        else:
            return False, f"Invalid action: {request.action}", None

        # Update database
        await self.db.execute(
            update(SkillProfile)
            .where(SkillProfile.profile_id == request.profile_id)
            .values(skills=skills)
        )

        # Create audit log
        audit_log = SkillAuditLog(
            profile_id=request.profile_id,
            skill_name=request.skill_name,
            action=request.action,
            previous_value=previous_state,
            new_value=skills[skill_index]
        )
        self.db.add(audit_log)

        await self.db.commit()

        updated_skill = SkillItem(**skills[skill_index])
        return True, message, updated_skill
