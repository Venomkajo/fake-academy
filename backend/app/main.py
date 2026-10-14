import sqlalchemy as sa
from fastapi import Depends, FastAPI

from app.database import get_db

app = FastAPI(title="Fake Academy API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/db")
def health_db(db=Depends(get_db)):
    try:
        # Simple query to check database connectivity
        db.execute(sa.text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}