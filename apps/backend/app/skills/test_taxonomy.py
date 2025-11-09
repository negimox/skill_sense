"""Test script to verify ESCO taxonomy loading and lookup"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.skills.taxonomy import get_taxonomy_mapper

def test_taxonomy():
    """Test taxonomy mapper functionality"""
    print("=" * 60)
    print("ESCO Taxonomy Mapper Test")
    print("=" * 60)

    # Get mapper instance
    mapper = get_taxonomy_mapper()

    # Test 1: Get all skills count
    all_skills = mapper.get_all_skills()
    print(f"\n✓ Total skills loaded: {len(all_skills)}")

    # Test 2: Test curated skills
    test_skills = [
        "Python",
        "JavaScript",
        "React",
        "Docker",
        "SQL",
        "Machine Learning",
        "Git"
    ]

    print("\n" + "=" * 60)
    print("Testing Curated Skills:")
    print("=" * 60)

    for skill in test_skills:
        mapping = mapper.get_mapping(skill)
        if mapping:
            print(f"\n✓ {skill}:")
            print(f"  ESCO ID: {mapping.get('esco_id')}")
            print(f"  URI: {mapping.get('esco_uri')}")
            print(f"  Category: {mapping.get('category')}")
            print(f"  Aliases: {', '.join(mapping.get('aliases', [])[:3])}")
        else:
            print(f"\n✗ {skill}: NOT FOUND")

    # Test 3: Test ESCO skills
    esco_test_skills = [
        "programming",
        "software development",
        "web development",
        "database management",
        "cloud computing"
    ]

    print("\n" + "=" * 60)
    print("Testing ESCO Skills:")
    print("=" * 60)

    for skill in esco_test_skills:
        mapping = mapper.get_mapping(skill)
        if mapping:
            print(f"\n✓ {skill}:")
            print(f"  Matched: {mapping.get('skill_name')}")
            print(f"  ESCO ID: {mapping.get('esco_id')}")
            print(f"  Category: {mapping.get('category')}")
        else:
            print(f"\n✗ {skill}: NOT FOUND")
            # Try to find similar
            similar = mapper.find_similar_skills(skill, limit=3)
            if similar:
                print(f"  Similar: {', '.join(similar[:3])}")

    # Test 4: Case insensitivity
    print("\n" + "=" * 60)
    print("Testing Case Insensitivity:")
    print("=" * 60)

    case_tests = [
        ("python", "PYTHON", "Python"),
        ("javascript", "JavaScript", "JAVASCRIPT"),
    ]

    for variants in case_tests:
        results = [mapper.get_esco_id(v) for v in variants]
        if all(r == results[0] for r in results):
            print(f"✓ {variants[0]}: All variants match ({results[0]})")
        else:
            print(f"✗ {variants[0]}: Variants don't match: {results}")

    # Test 5: Performance check
    print("\n" + "=" * 60)
    print("Performance Test:")
    print("=" * 60)

    import time

    start = time.time()
    for _ in range(1000):
        mapper.get_mapping("Python")
    elapsed = time.time() - start

    print(f"✓ 1000 lookups in {elapsed:.4f} seconds")
    print(f"  Average: {elapsed/1000*1000:.4f} ms per lookup")

    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_taxonomy()
