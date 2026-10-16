import sqlalchemy as sa
from fastapi import Depends, FastAPI

from app.database import get_db
from app.routers import auth

app = FastAPI(title="Fake Academy API")

# Mount every route group (URL prefix) here.
app.include_router(auth.router)

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