from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import preguntas, desempenos
from app.database import init_db

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="API para generar preguntas de evaluación usando IA (Gemini y ChatGPT)",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

# Include routers
app.include_router(preguntas.router, prefix="/api/preguntas", tags=["Preguntas"])
app.include_router(desempenos.router, prefix="/api/desempenos", tags=["Desempeños"])




@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

# Mount frontend static files
import os
from fastapi.staticfiles import StaticFiles

# Absolute path to frontend/dist relative to this file
frontend_dist = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../frontend/dist")

# Ensure the directory exists before mounting to avoid errors during development if not built
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")
