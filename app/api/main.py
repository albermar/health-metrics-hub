from fastapi import FastAPI
#from fastapi import APIRouter
from app.api.routers import kpis, upload

from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="Health Metrics Hub API", version="1.0.0", debug=True)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later to your streamlit URL
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Include routers
app.include_router(kpis.router, prefix="/api", tags=["KPIs"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])


