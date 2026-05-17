import os
import subprocess
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Persona AI API")


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


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
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)
