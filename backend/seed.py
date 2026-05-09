import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, AsyncSessionLocal, Base
from app import models, auth

async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Create an admin user
        admin = models.User(
            full_name="Admin User",
            email="admin@techkraft.com",
            hashed_password=auth.get_password_hash("admin123"),
            role="admin"
        )
        # Create a reviewer user
        reviewer = models.User(
            full_name="Reviewer User",
            email="reviewer@techkraft.com",
            hashed_password=auth.get_password_hash("reviewer123"),
            role="reviewer"
        )
        db.add_all([admin, reviewer])
        await db.commit()

        # Create candidates
        c1 = models.Candidate(
            name="Alice Johnson",
            email="alice@example.com",
            role_applied="Backend Engineer",
            status="new",
            skills=["Python", "FastAPI", "Docker"],
            internal_notes="Recommended by Bob. Good background."
        )
        c2 = models.Candidate(
            name="Bob Smith",
            email="bob@example.com",
            role_applied="Frontend Engineer",
            status="reviewed",
            skills=["React", "TypeScript", "Vite"],
            internal_notes="Need to check his design portfolio."
        )
        db.add_all([c1, c2])
        await db.commit()

        print("Database seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed())
