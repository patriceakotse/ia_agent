from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.models.database import engine, Base
from app.api import auth, projects, sessions, teams, git, preview, alerts, llm_settings, admin_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: créer les tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup si nécessaire


app = FastAPI(
    title=settings.APP_NAME,
    description="Plateforme SaaS d'Orchestration de Développement Pilotée par IA",
    version="0.1.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(projects.router, prefix=settings.API_V1_PREFIX)
app.include_router(sessions.router, prefix=settings.API_V1_PREFIX)
app.include_router(teams.router, prefix=settings.API_V1_PREFIX)
app.include_router(git.router, prefix=settings.API_V1_PREFIX)
app.include_router(preview.router, prefix=settings.API_V1_PREFIX)
app.include_router(alerts.router, prefix=settings.API_V1_PREFIX)
app.include_router(llm_settings.router, prefix=settings.API_V1_PREFIX)
app.include_router(admin_settings.router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )