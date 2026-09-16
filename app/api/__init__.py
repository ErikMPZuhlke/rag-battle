"""Aggregates all API routers under a single `api_router`."""
from fastapi import APIRouter

from app.api.routes import ask, health, ingest, retrieve

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(ask.router)
api_router.include_router(retrieve.router)
api_router.include_router(ingest.router)
