"""
Main FastAPI application.
"""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from drug_trafficking_osint.interfaces.api.routes import router

app = FastAPI(
    title="AI OSINT Drug Trafficking Detection API",
    version="1.0.0",
    description="AI-powered OSINT framework for drug trafficking detection.",
)

app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    """
    Root endpoint.
    """
    return {"message": "AI OSINT API is running successfully."}


def run() -> None:
    uvicorn.run(
        "drug_trafficking_osint.interfaces.api.main:app",
        host="127.0.0.1",
        port=8000,
    )
