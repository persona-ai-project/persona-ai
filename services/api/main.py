import os
import subprocess
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Persona AI API")


@app.get("/healthz")
def health_check():
    return {"status": "ok"}

@app.get("/ping")
def ping():
    return {"pong": True}

@app.get("/")
def root():
    return {"message": "Persona AI API is running"}


def run_migrations():
    print("Running Alembic migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=os.path.dirname(__file__),
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print("Migration error:", result.stderr)
        raise RuntimeError("Migrations failed")
    print("Migrations complete.")


if __name__ == "__main__":
    run_migrations()
    reload = os.getenv("RELOAD", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8001")),
        reload=reload
    )