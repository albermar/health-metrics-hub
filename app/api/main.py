from fastapi import FastAPI
#from fastapi import APIRouter
from app.api.routers import kpis, upload


app = FastAPI(title="Health Metrics Hub API", version="1.0.0", debug=True)

#Include routers
app.include_router(kpis.router, prefix="/api", tags=["KPIs"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])


