# TechKraft Candidate Scoring Dashboard

This is a full-stack candidate scoring and review dashboard built for the TechKraft internal recruitment workflow.

## Setup and Run Instructions

1.  **Environment Variables**: Copy the example file.
    ```bash
    cp .env.example .env
    ```
2.  **Backend Local Setup (optional)**: Create a Python virtual environment and install dependencies.
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    python3 -m pip install -r requirements.txt
    ```
3.  **Start Services**: Use Docker Compose to build and start the backend and frontend.
    ```bash
    docker compose up --build
    ```
4.  **Seed Data**: (Optional) Populate the database with initial candidates and users.
    ```bash
    docker compose exec backend python seed.py
    ```
4.  **Access**:
    *   Frontend: `http://localhost:5173`
    *   Backend API Docs: `http://localhost:8000/docs`

## Debugging Signal: In-Memory Filtering vs SQL

**Issue Identified:**
The provided code snippet fetches all candidates into Python memory and then applies filtering and pagination:

```python
all_candidates = db.execute("SELECT * FROM candidates").fetchall()
filtered = [c for c in all_candidates if c["status"] == status]
```

**Why it matters at scale:**
Loading the entire `candidates` table into memory is highly inefficient. If there are 100,000 candidates, the backend must deserialize 100,000 records, map them to Python objects, run a Python loop for filtering, slice the array for pagination, and discard 99,980 records. This will lead to massive CPU spikes, huge memory consumption, and eventually Out-Of-Memory (OOM) crashes as concurrent requests scale.

**Correct Approach:**
Push filtering and pagination down to the database level using standard SQL constructs: `WHERE` clauses for filtering and `LIMIT`/`OFFSET` for pagination.

```python
# Correct approach mapping roughly to SQLAlchemy or raw DB API:
query = "SELECT * FROM candidates WHERE status = ? LIMIT ? OFFSET ?"
# Execution will vary based on ORM/Library, but the SQL pushdown is key.
```

## Architecture Decision Record (ADR)

1.  **Context**: Choosing the backend web framework.
    *   **Decision**: FastAPI.
    *   **Trade-off**: FastAPI offers high performance, automatic OpenAPI documentation, and robust async support. The trade-off is a slightly steeper learning curve compared to simple Flask setups and reliance on Pydantic for validation.

2.  **Context**: Choosing the database for a portable take-home assignment.
    *   **Decision**: SQLite via SQLAlchemy (Async).
    *   **Trade-off**: Chose SQLite to ensure the project works out-of-the-box for reviewers without requiring a separate PostgreSQL container. The trade-off is SQLite's concurrency limitations, but for a mock dashboard, this is an acceptable compromise to optimize for reviewer experience.

3.  **Context**: Swagger Authentication UI.
    *   **Decision**: `HTTPBearer` over `OAuth2PasswordBearer`.
    *   **Trade-off**: Switched to `HTTPBearer` to allow direct pasting of JWT tokens into the Swagger "Authorize" dialog, which is more common for quick API testing. This changes the Swagger UI flow from a username/password form to a simple token input.

## Learning Reflection

During this project, I successfully implemented **Server-Sent Events (SSE)** to provide real-time score updates to the admin dashboard, ensuring a dynamic and responsive user experience. If given more time, I would further explore implementing a more robust soft-delete mechanism with audit logs to track who performed the archival of a candidate record and when.

## Example API Calls

You can use `curl` to test the API directly once it's running:

```bash
# 1. Register a new user
curl -X 'POST' \
  'http://localhost:8000/auth/register' \
  -H 'Content-Type: application/json' \
  -d '{
  "full_name": "Jane Doe",
  "email": "jane@example.com",
  "password": "securepassword123"
}'

# 2. Get Candidates (Requires Token)
curl -X 'GET' \
  'http://localhost:8000/candidates?status=new&page=1&page_size=20' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <YOUR_TOKEN>'

# 3. Score a Candidate (Requires Token)
curl -X 'POST' \
  'http://localhost:8000/candidates/<CANDIDATE_ID>/scores' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <YOUR_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
  "category": "Technical",
  "score": 5,
  "note": "Excellent problem-solving skills."
}'
```