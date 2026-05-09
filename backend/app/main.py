from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, candidates
from app.database import engine, Base

# Import models to ensure they are registered with SQLAlchemy
from app import models

app = FastAPI(title="TechKraft API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev purposes, allows Vite frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(candidates.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "TechKraft API is running."}
