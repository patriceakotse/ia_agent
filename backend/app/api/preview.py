from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.models.database import get_db
from app.models.models import Project, User
from app.services.preview_deployment import preview_service
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/projects/{project_id}/previews", tags=["Preview Deployment"])


# ==================== SCHEMAS ====================

class CreatePreviewRequest(BaseModel):
    workspace_path: str
    dockerfile_path: Optional[str] = None
    build_command: Optional[str] = None
    run_command: Optional[str] = None
    env_vars: Optional[dict] = None


class PreviewResponse(BaseModel):
    id: str
    project_id: int
    status: str
    port: int
    url: Optional[str]
    created_at: str
    expires_at: str


# ==================== ROUTES ====================

@router.get("", response_model=List[PreviewResponse])
async def list_previews(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les instances de prévisualisation d'un projet."""
    instances = preview_service.list_instances(project_id)
    
    return [
        PreviewResponse(
            id=i.id,
            project_id=i.project_id,
            status=i.status,
            port=i.port,
            url=i.url,
            created_at=i.created_at.isoformat(),
            expires_at=i.expires_at.isoformat()
        )
        for i in instances
    ]


@router.post("", response_model=PreviewResponse, status_code=status.HTTP_201_CREATED)
async def create_preview(
    project_id: int,
    preview_data: CreatePreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crée une nouvelle instance de prévisualisation."""
    # Vérifier que le projet existe et appartient à l'utilisateur
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    
    # Vérifier le nombre d'instances actives
    active_count = len([
        i for i in preview_service.list_instances(project_id)
        if i.status == "running" or i.status == "building"
    ])
    
    if active_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nombre maximum d'instances actives atteint (3)"
        )
    
    instance = await preview_service.create_preview(
        project_id=project_id,
        workspace_path=preview_data.workspace_path,
        dockerfile_path=preview_data.dockerfile_path,
        build_command=preview_data.build_command,
        run_command=preview_data.run_command,
        env_vars=preview_data.env_vars
    )
    
    return PreviewResponse(
        id=instance.id,
        project_id=instance.project_id,
        status=instance.status,
        port=instance.port,
        url=instance.url,
        created_at=instance.created_at.isoformat(),
        expires_at=instance.expires_at.isoformat()
    )


@router.get("/{preview_id}", response_model=PreviewResponse)
async def get_preview(
    project_id: int,
    preview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère les détails d'une instance de prévisualisation."""
    instance = preview_service.get_instance(preview_id)
    
    if not instance or instance.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance non trouvée")
    
    return PreviewResponse(
        id=instance.id,
        project_id=instance.project_id,
        status=instance.status,
        port=instance.port,
        url=instance.url,
        created_at=instance.created_at.isoformat(),
        expires_at=instance.expires_at.isoformat()
    )


@router.get("/{preview_id}/logs")
async def get_preview_logs(
    project_id: int,
    preview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère les logs d'une instance."""
    instance = preview_service.get_instance(preview_id)
    
    if not instance or instance.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance non trouvée")
    
    logs = await preview_service.get_logs(preview_id)
    
    return {"logs": logs, "status": instance.status}


@router.post("/{preview_id}/stop")
async def stop_preview(
    project_id: int,
    preview_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Arrête une instance de prévisualisation."""
    instance = preview_service.get_instance(preview_id)
    
    if not instance or instance.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Instance non trouvée")
    
    success = await preview_service.stop_preview(preview_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'arrêt de l'instance"
        )
    
    return {"message": "Instance arrêtée"}


@router.post("/cleanup")
async def cleanup_expired_previews(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Nettoie les instances expirées."""
    # Vérifier que le projet existe
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    
    count = await preview_service.cleanup_expired()
    
    return {"message": f"{count} instance(s) expirée(s) nettoyée(s)"}