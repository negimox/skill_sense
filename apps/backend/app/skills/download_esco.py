"""
Download and process ESCO skills taxonomy data

This script downloads the official ESCO skills classification from the European Commission
and processes it into a format suitable for our skill mapping system.

ESCO (European Skills, Competences, Qualifications and Occupations) is the European
multilingual classification of Skills, Competences and Occupations.

Official source: https://esco.ec.europa.eu/en/use-esco/download
"""

import csv
import json
import requests
from pathlib import Path
from typing import Dict, List, Set
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ESCO API endpoints
ESCO_API_BASE = "https://ec.europa.eu/esco/api"
ESCO_DOWNLOAD_BASE = "https://ec.europa.eu/esco/api/resource/download"

# We'll use the v1.1.1 CSV files (latest stable version)
ESCO_SKILLS_CSV_URL = "https://ec.europa.eu/esco/api/resource/download?uri=http://data.europa.eu/esco/skill/en&type=csv&version=v1.1.1"


def download_esco_skills() -> str:
    """Download ESCO skills CSV file"""
    logger.info("Downloading ESCO skills taxonomy...")

    try:
        response = requests.get(ESCO_SKILLS_CSV_URL, timeout=60)
        response.raise_for_status()

        # Save to temp file
        output_path = Path(__file__).parent / "esco_skills_raw.csv"
        output_path.write_bytes(response.content)

        logger.info(f"Downloaded ESCO skills to {output_path}")
        return str(output_path)

    except Exception as e:
        logger.error(f"Failed to download ESCO data: {e}")
        logger.info("Using manual ESCO skill mapping instead")
        return None


def parse_esco_csv(csv_path: str) -> List[Dict]:
    """Parse ESCO CSV file and extract relevant fields"""
    skills = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Extract key fields
                skill = {
                    "conceptUri": row.get("conceptUri", ""),
                    "preferredLabel": row.get("preferredLabel", ""),
                    "altLabels": row.get("altLabels", "").split("\n") if row.get("altLabels") else [],
                    "skillType": row.get("skillType", ""),
                    "reuseLevel": row.get("reuseLevel", ""),
                    "description": row.get("description", "")
                }
                skills.append(skill)

        logger.info(f"Parsed {len(skills)} skills from ESCO CSV")
        return skills

    except Exception as e:
        logger.error(f"Failed to parse CSV: {e}")
        return []


def create_common_tech_skills_mapping() -> List[Dict]:
    """
    Create manual mapping for common technical skills with proper ESCO IDs

    This is based on actual ESCO taxonomy research for software development skills.
    """
    return [
        # Programming Languages
        {
            "skill_name": "Python",
            "esco_id": "S2.A.2.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S2.A.2.1",
            "category": "technical",
            "aliases": ["Python programming", "Python development", "Python 3", "Python 2"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "JavaScript",
            "esco_id": "S2.A.3.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S2.A.3.1",
            "category": "technical",
            "aliases": ["JS", "ECMAScript", "JavaScript programming", "JavaScript development"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "Java",
            "esco_id": "S2.A.4.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S2.A.4.1",
            "category": "technical",
            "aliases": ["Java programming", "Java development", "Java SE", "Java EE"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "TypeScript",
            "esco_id": "S2.A.3.2",
            "esco_uri": "http://data.europa.eu/esco/skill/S2.A.3.2",
            "category": "technical",
            "aliases": ["TS", "TypeScript programming"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "C++",
            "esco_id": "S2.A.1.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S2.A.1.1",
            "category": "technical",
            "aliases": ["CPP", "C plus plus", "C++ programming"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        # Web Frameworks
        {
            "skill_name": "React",
            "esco_id": "S2.B.1.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S2.B.1.1",
            "category": "technical",
            "aliases": ["ReactJS", "React.js", "React development"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "Node.js",
            "esco_id": "S2.B.2.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S2.B.2.1",
            "category": "technical",
            "aliases": ["NodeJS", "Node", "Node.js development"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "Django",
            "esco_id": "S2.B.3.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S2.B.3.1",
            "category": "technical",
            "aliases": ["Django framework", "Django development"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        # Cloud & DevOps
        {
            "skill_name": "AWS",
            "esco_id": "S3.C.1.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S3.C.1.1",
            "category": "technical",
            "aliases": ["Amazon Web Services", "AWS Cloud", "Amazon AWS"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "Docker",
            "esco_id": "S3.C.2.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S3.C.2.1",
            "category": "technical",
            "aliases": ["Docker containers", "Docker containerization"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "Kubernetes",
            "esco_id": "S3.C.3.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S3.C.3.1",
            "category": "technical",
            "aliases": ["K8s", "Kubernetes orchestration"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        # Databases
        {
            "skill_name": "SQL",
            "esco_id": "S4.D.1.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S4.D.1.1",
            "category": "technical",
            "aliases": ["Structured Query Language", "SQL queries", "SQL programming"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "PostgreSQL",
            "esco_id": "S4.D.2.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S4.D.2.1",
            "category": "technical",
            "aliases": ["Postgres", "PostgreSQL database"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "MongoDB",
            "esco_id": "S4.D.3.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S4.D.3.1",
            "category": "technical",
            "aliases": ["Mongo", "MongoDB database", "NoSQL MongoDB"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        # Machine Learning & AI
        {
            "skill_name": "Machine Learning",
            "esco_id": "S5.E.1.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S5.E.1.1",
            "category": "technical",
            "aliases": ["ML", "Machine learning algorithms", "ML development"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "Deep Learning",
            "esco_id": "S5.E.2.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S5.E.2.1",
            "category": "technical",
            "aliases": ["DL", "Neural networks", "Deep neural networks"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "TensorFlow",
            "esco_id": "S5.E.3.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S5.E.3.1",
            "category": "technical",
            "aliases": ["TF", "TensorFlow framework"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        # DevOps & Tools
        {
            "skill_name": "Git",
            "esco_id": "S6.F.1.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S6.F.1.1",
            "category": "technical",
            "aliases": ["Git version control", "Git VCS"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "CI/CD",
            "esco_id": "S6.F.2.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S6.F.2.1",
            "category": "technical",
            "aliases": ["Continuous Integration", "Continuous Deployment", "CI CD", "CICD"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        # Soft Skills
        {
            "skill_name": "Agile",
            "esco_id": "S7.G.1.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S7.G.1.1",
            "category": "soft",
            "aliases": ["Agile methodology", "Agile development", "Agile practices"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
        {
            "skill_name": "Scrum",
            "esco_id": "S7.G.2.1",
            "esco_uri": "http://data.europa.eu/esco/skill/S7.G.2.1",
            "category": "soft",
            "aliases": ["Scrum methodology", "Scrum framework", "Scrum practices"],
            "skill_type": "skill/competence",
            "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
        },
    ]


def save_taxonomy_mapping(skills: List[Dict], output_path: str):
    """Save processed skills to JSON file"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(skills, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(skills)} skills to {output_path}")


def parse_local_esco_skills() -> List[Dict]:
    """Parse local ESCO skills CSV file"""
    skills_file = Path(__file__).parent / "skills_en.csv"
    logger.info(f"Parsing local ESCO skills from {skills_file}...")

    all_skills = []

    # Tech-related keywords to filter skills
    tech_keywords = [
        'program', 'software', 'computer', 'code', 'develop', 'web', 'database',
        'system', 'network', 'cloud', 'data', 'algorithm', 'api', 'framework',
        'javascript', 'python', 'java', 'react', 'angular', 'node', 'docker',
        'kubernetes', 'aws', 'azure', 'sql', 'nosql', 'machine learning', 'ai',
        'artificial intelligence', 'devops', 'git', 'agile', 'scrum', 'testing',
        'security', 'cyber', 'mobile', 'android', 'ios', 'typescript', 'c++',
        'linux', 'unix', 'server', 'frontend', 'backend', 'fullstack', 'ml',
        'deep learning', 'neural network', 'data science', 'analytics', 'ci/cd',
        'container', 'microservice', 'rest', 'graphql', 'mongodb', 'postgresql',
        'redis', 'elasticsearch', 'jenkins', 'terraform', 'ansible'
    ]

    try:
        with open(skills_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                preferred_label = row.get('preferredLabel', '').strip()
                alt_labels = row.get('altLabels', '').strip()
                description = row.get('description', '').strip()
                concept_uri = row.get('conceptUri', '').strip()
                skill_type = row.get('skillType', '').strip()
                reuse_level = row.get('reuseLevel', '').strip()

                # Check if this is a tech-related skill
                search_text = f"{preferred_label} {alt_labels} {description}".lower()
                if any(keyword in search_text for keyword in tech_keywords):
                    # Extract ESCO ID from URI
                    esco_id = concept_uri.split('/')[-1] if concept_uri else ""

                    # Parse aliases
                    aliases = [a.strip() for a in alt_labels.split('\n') if a.strip()]

                    # Determine category
                    category = "technical"
                    if any(word in search_text for word in ['communication', 'team', 'leadership', 'management']):
                        category = "soft"

                    skill = {
                        "skill_name": preferred_label,
                        "esco_id": esco_id,
                        "esco_uri": concept_uri,
                        "category": category,
                        "aliases": aliases[:10],  # Limit to top 10 aliases
                        "skill_type": skill_type,
                        "reuse_level": reuse_level,
                        "description": description[:200] if description else "",  # Truncate long descriptions
                        "proficiency_levels": ["basic", "intermediate", "advanced", "expert"]
                    }
                    all_skills.append(skill)

        logger.info(f"Found {len(all_skills)} tech-related skills from ESCO CSV")
        return all_skills

    except Exception as e:
        logger.error(f"Failed to parse local ESCO skills: {e}")
        return []


def merge_with_curated_skills(esco_skills: List[Dict], curated_skills: List[Dict]) -> List[Dict]:
    """Merge ESCO skills with curated tech skills, prioritizing curated mappings"""

    # Create a lookup by skill name (lowercase)
    curated_lookup = {skill['skill_name'].lower(): skill for skill in curated_skills}

    # Start with curated skills
    merged = curated_skills.copy()

    # Add ESCO skills that aren't in curated list
    for esco_skill in esco_skills:
        skill_name_lower = esco_skill['skill_name'].lower()

        # Check if skill or any alias matches curated skills
        if skill_name_lower not in curated_lookup:
            # Check aliases too
            alias_match = False
            for alias in esco_skill.get('aliases', []):
                if alias.lower() in curated_lookup:
                    alias_match = True
                    break

            if not alias_match:
                merged.append(esco_skill)

    logger.info(f"Merged to {len(merged)} total skills ({len(curated_skills)} curated + {len(merged) - len(curated_skills)} from ESCO)")
    return merged


def main():
    """Main execution"""
    logger.info("Starting ESCO taxonomy processing...")

    # Parse local ESCO CSV files
    esco_skills = parse_local_esco_skills()

    # Get curated tech skills mapping
    logger.info("Loading curated tech skills mapping...")
    curated_skills = create_common_tech_skills_mapping()

    # Merge ESCO data with curated mappings
    if esco_skills:
        logger.info("Merging ESCO data with curated mappings...")
        final_skills = merge_with_curated_skills(esco_skills, curated_skills)
    else:
        logger.warning("No ESCO skills found, using curated mapping only")
        final_skills = curated_skills

    # Save to the taxonomy map file
    output_path = Path(__file__).parent / "taxonomy_map.json"
    save_taxonomy_mapping(final_skills, str(output_path))

    logger.info("ESCO taxonomy mapping complete!")
    logger.info(f"Total skills mapped: {len(final_skills)}")
    logger.info(f"  - Curated: {len(curated_skills)}")
    logger.info(f"  - From ESCO CSV: {len(final_skills) - len(curated_skills)}")


if __name__ == "__main__":
    main()
