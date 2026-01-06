from fastapi import FastAPI
from fastapi import APIRouter
from app.api.routers import kpis


app = FastAPI(title="Health Metrics Hub API", version="1.0.0")

#Include routers
app.include_router(kpis.router, prefix="/api", tags=["KPIs"])


