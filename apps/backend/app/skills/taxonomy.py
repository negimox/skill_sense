"""Skill taxonomy utilities for mapping skills to ESCO IDs"""
import json
import os
from typing import Optional, Dict, List
from pathlib import Path


class TaxonomyMapper:
    """Maps skill names to ESCO taxonomy IDs"""

    def __init__(self):
        self._taxonomy_map: Dict[str, Dict] = {}
        self._load_taxonomy()

    def _load_taxonomy(self):
        """Load taxonomy mappings from JSON file"""
        taxonomy_file = Path(__file__).parent / "taxonomy_map.json"
        try:
            with open(taxonomy_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Handle both array format and object format
                mappings = data if isinstance(data, list) else data.get("mappings", [])

                # Create index by skill name (case-insensitive)
                for mapping in mappings:
                    skill_name = mapping["skill_name"].lower()
                    self._taxonomy_map[skill_name] = mapping

                    # Also index by aliases
                    for alias in mapping.get("aliases", []):
                        if alias:  # Skip empty aliases
                            self._taxonomy_map[alias.lower()] = mapping

                print(f"Loaded {len(self._taxonomy_map)} skill mappings from ESCO taxonomy")
        except FileNotFoundError:
            print("Warning: Taxonomy file not found, continuing without ESCO mappings")
            pass
        except Exception as e:
            print(f"Error loading taxonomy: {e}")
            pass

    def get_mapping(self, skill_name: str) -> Optional[Dict]:
        """Get ESCO mapping for a skill name"""
        return self._taxonomy_map.get(skill_name.lower())

    def get_esco_id(self, skill_name: str) -> Optional[str]:
        """Get ESCO ID for a skill name"""
        mapping = self.get_mapping(skill_name)
        return mapping.get("esco_id") if mapping else None

    def get_category(self, skill_name: str) -> str:
        """Get category for a skill (technical, soft, domain)"""
        mapping = self.get_mapping(skill_name)
        return mapping.get("category", "technical") if mapping else "technical"

    def find_similar_skills(self, skill_name: str, limit: int = 5) -> List[str]:
        """Find similar skill names in taxonomy"""
        skill_lower = skill_name.lower()
        matches = []

        for mapped_skill in self._taxonomy_map.keys():
            if skill_lower in mapped_skill or mapped_skill in skill_lower:
                matches.append(mapped_skill)
                if len(matches) >= limit:
                    break

        return matches

    def get_all_skills(self) -> List[str]:
        """Get all mapped skill names"""
        return list(self._taxonomy_map.keys())

    def get_all_mappings(self) -> List[Dict]:
        """Return unique taxonomy mapping records"""
        seen: set[int] = set()
        mappings: List[Dict] = []

        for mapping in self._taxonomy_map.values():
            mapping_id = id(mapping)
            if mapping_id in seen:
                continue
            seen.add(mapping_id)
            mappings.append(mapping)

        return mappings


# Global instance
_taxonomy_mapper = None

def get_taxonomy_mapper() -> TaxonomyMapper:
    """Get singleton taxonomy mapper instance"""
    global _taxonomy_mapper
    if _taxonomy_mapper is None:
        _taxonomy_mapper = TaxonomyMapper()
    return _taxonomy_mapper
