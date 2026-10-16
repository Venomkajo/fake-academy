import sqlalchemy as sa
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import CORS_ORIGINS
from app.database import get_db
from app.routers import auth, users

app = FastAPI(title="Fake Academy API")

# CORS. The frontend (React on :3000) and this API (:8001) are
# different ORIGINS (scheme+host+port), and browsers block
# cross-origin requests unless the server explicitly allows them.
# CORSMiddleware answers the browser's preflight OPTIONS requests.
# allow_origins is an explicit LIST (not "*") so we can add/remove
# environments deliberately; allow_credentials lets cookies fly later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount every route group (URL prefix) here.
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/health")
def health():
    # Liveness probe: just checks the API process is up.
    return {"status": "ok"}

@app.get("/health/db")
def health_db(db=Depends(get_db)):
    # Readiness probe: also checks the database actually answers.
    try:
        # Simple query to check database connectivity
        db.execute(sa.text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}