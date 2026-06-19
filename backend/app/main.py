from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.models.database import engine, Base, SessionLocal
from app.models.models import User, Team, Project
from app.services.auth_service import get_password_hash
from app.api import auth, projects, sessions, teams, git, preview, alerts, llm_settings, admin_settings


def seed_default_admin():
    """Crée un admin par défaut si aucun utilisateur n'existe."""
    db = SessionLocal()
    try:
        # Vérifier si un admin existe déjà
        existing_admin = db.query(User).filter(User.email == "admin@example.com").first()
        if not existing_admin:
            admin = User(
                email="admin@example.com",
                username="admin",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator",
                is_active=True,
                is_superuser=True
            )
            db.add(admin)
            db.commit()
            print("✓ Admin par défaut créé: admin@example.com / admin123")
        else:
            print("✓ Admin existe déjà")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: créer les tables et seed admin
    Base.metadata.create_all(bind=engine)
    seed_default_admin()
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