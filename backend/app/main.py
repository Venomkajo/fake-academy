from fastapi import FastAPI

app = FastAPI(title="Fake Academy API")

@app.get("/health")
def health():
    return {"status": "ok"}