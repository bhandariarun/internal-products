import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse
from typing import Optional

from app import schemas, models, auth
from app.database import get_db

router = APIRouter(prefix="/candidates", tags=["candidates"])

# For SSE events
score_events = {}

@router.get("", response_model=schemas.PaginatedCandidates)
async def list_candidates(
    status: Optional[str] = None,
    role_applied: Optional[str] = None,
    skill: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    query = select(models.Candidate).where(models.Candidate.deleted_at.is_(None))
    
    if status:
        query = query.where(models.Candidate.status == status)
    if role_applied:
        query = query.where(models.Candidate.role_applied.ilike(f"%{role_applied}%"))
    if keyword:
        # Simple search across name and email
        query = query.where(
            (models.Candidate.name.ilike(f"%{keyword}%")) | 
            (models.Candidate.email.ilike(f"%{keyword}%"))
        )
    # Note: JSON filtering for skills varies by DB, for SQLite a simple text search might suffice or we skip exact JSON array querying for this mock
    if skill:
        # basic workaround for sqlite json text
        query = query.where(models.Candidate.skills.cast(models.String).ilike(f"%{skill}%"))

    # Pagination logic pushed down to SQL
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    
    result = await db.execute(query)
    candidates = result.scalars().all()

    return {
        "items": candidates,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{id}", response_model=schemas.CandidateDetailResponse)
async def get_candidate(id: str, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    result = await db.execute(
        select(models.Candidate)
        .options(selectinload(models.Candidate.scores))
        .where(models.Candidate.id == id, models.Candidate.deleted_at.is_(None))
    )
    candidate = result.scalars().first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    scores = candidate.scores
    
    # Filter scores and notes based on role
    internal_notes = candidate.internal_notes
    if current_user.role != "admin":
        internal_notes = None
        scores = [s for s in scores if s.reviewer_id == current_user.id]

    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "role_applied": candidate.role_applied,
        "status": candidate.status,
        "skills": candidate.skills,
        "internal_notes": internal_notes,
        "created_at": candidate.created_at,
        "scores": scores
    }

@router.post("/{id}/scores", response_model=schemas.ScoreResponse)
async def create_score(id: str, score: schemas.ScoreCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    result = await db.execute(select(models.Candidate).where(models.Candidate.id == id, models.Candidate.deleted_at.is_(None)))
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    new_score = models.Score(
        candidate_id=id,
        category=score.category,
        score=score.score,
        note=score.note,
        reviewer_id=current_user.id
    )
    db.add(new_score)
    await db.commit()
    await db.refresh(new_score)
    
    # Trigger SSE Event
    if id in score_events:
        for q in score_events[id]:
            await q.put({"event": "new_score", "data": str(new_score.id)})

    return new_score

@router.post("/{id}/summary")
async def generate_summary(id: str, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    result = await db.execute(select(models.Candidate).where(models.Candidate.id == id, models.Candidate.deleted_at.is_(None)))
    if not result.scalars().first():
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # Mock AI Call
    await asyncio.sleep(2)
    return {"summary": "This candidate shows strong potential in system design and backend technologies. They clearly communicated tradeoffs during the technical discussion."}

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_candidate(id: str, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(auth.get_current_admin)):
    result = await db.execute(select(models.Candidate).where(models.Candidate.id == id, models.Candidate.deleted_at.is_(None)))
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    candidate.deleted_at = models.utcnow()
    candidate.status = "archived"
    await db.commit()

@router.get("/{id}/stream")
async def stream_scores(id: str, current_user: models.User = Depends(auth.get_current_user)):
    if id not in score_events:
        score_events[id] = []
    
    q = asyncio.Queue()
    score_events[id].append(q)

    async def event_generator():
        try:
            while True:
                # Wait for new score
                data = await q.get()
                yield data
        except asyncio.CancelledError:
            score_events[id].remove(q)
            if not score_events[id]:
                del score_events[id]

    return EventSourceResponse(event_generator())
