import asyncio
import json
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
        .where(models.Candidate.id == id, models.Candidate.deleted_at.is_(None))
    )
    candidate = result.scalars().first()
    
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # Filter scores and notes based on role
    internal_notes = candidate.internal_notes
    if current_user.role != "admin":
        internal_notes = None

    return {
        "id": candidate.id,
        "name": candidate.name,
        "email": candidate.email,
        "role_applied": candidate.role_applied,
        "status": candidate.status,
        "skills": candidate.skills,
        "internal_notes": internal_notes,
        "created_at": candidate.created_at,
        "scores": []  # Scores are streamed separately
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
    
    # Trigger SSE Event with full score data
    if id in score_events:
        score_data = json.dumps({
            "id": str(new_score.id),
            "category": new_score.category,
            "score": new_score.score,
            "note": new_score.note,
            "reviewer_id": str(new_score.reviewer_id),
            "created_at": new_score.created_at.isoformat()
        })
        for q in score_events[id]:
            await q.put({"event": "new_score", "data": score_data})

    return new_score

@router.post("/{id}/summary")
async def generate_summary(id: str, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    result = await db.execute(
        select(models.Candidate)
        .options(selectinload(models.Candidate.scores))
        .where(models.Candidate.id == id, models.Candidate.deleted_at.is_(None))
    )
    candidate = result.scalars().first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Simulate AI processing time
    await asyncio.sleep(2)

    skills = candidate.skills or []
    scores = candidate.scores or []
    
    # Calculate deeper insights
    if scores:
        avg_score = sum(s.score for s in scores) / len(scores)
        top_categories = sorted(scores, key=lambda x: x.score, reverse=True)
        strengths = [s.category for s in top_categories[:2] if s.score >= 4]
        concerns = [s.category for s in top_categories if s.score <= 2]
        
        notes = [s.note for s in scores if s.note]
        combined_notes = " ".join(notes)
        
        # Build a nuanced narrative
        intro = f"Analysis for {candidate.name} (Role: {candidate.role_applied}): "
        skill_analysis = f"The candidate demonstrates a solid technical foundation in {', '.join(skills[:3])}. " if skills else "The candidate's profile is currently being evaluated for technical alignment. "
        
        score_analysis = f"Based on {len(scores)} assessments, they have an overall rating of {avg_score:.1f}/5.0. "
        if strengths:
            score_analysis += f"Key strengths identified in {', '.join(strengths)}. "
        if concerns:
            score_analysis += f"Potential growth areas noted in {', '.join(concerns)}. "
            
        sentiment = "The reviewer sentiment is generally positive, highlighting their professional approach." if avg_score > 3.5 else "Initial feedback suggests some areas for further deep-dive in upcoming interviews."
        
        summary = f"{intro}\n\n{skill_analysis}{score_analysis}\n\nConclusion: {sentiment} {combined_notes[:200]}..."
    else:
        summary = (
            f"AI Preliminary Analysis for {candidate.name}:\n\n"
            f"The candidate has applied for the {candidate.role_applied} position. Their background includes skills in {', '.join(skills)}. "
            "Currently, there are no interview scores recorded. Recommendation: Schedule initial technical screening to validate core competencies and culture fit."
        )

    return {"summary": summary}

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
async def stream_scores(id: str, current_user: models.User = Depends(auth.get_current_user_optional), db: AsyncSession = Depends(get_db)):
    if id not in score_events:
        score_events[id] = []
    
    q = asyncio.Queue()
    score_events[id].append(q)

    async def event_generator():
        try:
            # Send current scores
            result = await db.execute(
                select(models.Score)
                .where(models.Score.candidate_id == id)
            )
            current_scores = result.scalars().all()
            scores_data = json.dumps([{
                "id": str(score.id),
                "category": score.category,
                "score": score.score,
                "note": score.note,
                "reviewer_id": str(score.reviewer_id),
                "created_at": score.created_at.isoformat()
            } for score in current_scores])
            yield {"event": "current_scores", "data": scores_data}
            
            while True:
                try:
                    # Wait for new score with a timeout for heartbeat
                    data = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield data
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield {"event": "ping", "data": "heartbeat"}
        except asyncio.CancelledError:
            if id in score_events and q in score_events[id]:
                score_events[id].remove(q)
                if not score_events[id]:
                    del score_events[id]
            raise

    return EventSourceResponse(event_generator())
