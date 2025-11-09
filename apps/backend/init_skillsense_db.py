#!/usr/bin/env python3
"""
Database initialization script for SkillSense
Creates tables for skill profiles and audit logs
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import async_engine
from app.models import Base


async def init_db():
    """Initialize database tables"""
    print("🔧 Initializing SkillSense database tables...")

    async with async_engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Database tables created successfully!")
    print("\nTables created:")
    print("  - skill_profiles")
    print("  - skill_audit_logs")
    print("\nYou can now start using SkillSense! 🧠")


if __name__ == "__main__":
    asyncio.run(init_db())
