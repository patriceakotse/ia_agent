from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db
from app.models.models import Project, Document, User
from app.models.document_versions import DocumentVersion
from app.schemas.schemas import DocumentResponse, DocumentUpdate
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/projects/{project_id}/documents", tags=["Documents"])


@router.get("/{doc_type}/versions", response_model=List[dict])
async def get_document_versions(
    project_id: int,
    doc_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère l'historique des versions d'un document."""
    # Vérifier l'accès au projet
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    # Récupérer le document
    document = db.query(Document).filter(
        Document.project_id == project_id,
        Document.doc_type == doc_type
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé"
        )
    
    # Récupérer les versions
    versions = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document.id
    ).order_by(DocumentVersion.version.desc()).all()
    
    return [
        {
            "id": v.id,
            "version": v.version,
            "content": v.content,
            "change_summary": v.change_summary,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "created_by_id": v.created_by_id
        }
        for v in versions
    ]


@router.post("/{doc_type}/restore/{version_number}", response_model=DocumentResponse)
async def restore_document_version(
    project_id: int,
    doc_type: str,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restaure une version antérieure du document."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    document = db.query(Document).filter(
        Document.project_id == project_id,
        Document.doc_type == doc_type
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé"
        )
    
    # Récupérer la version à restaurer
    version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document.id,
        DocumentVersion.version == version_number
    ).first()
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_number} non trouvée"
        )
    
    # Sauvegarder la version actuelle avant de restaurer
    current_version = DocumentVersion(
        document_id=document.id,
        version=document.version,
        content=document.content,
        change_summary=f"Restauration vers la version {version_number}",
        created_by_id=current_user.id
    )
    db.add(current_version)
    
    # Restorer le contenu
    document.content = version.content
    document.version = version_number + 1  # Incrémenter après restauration
    document.updated_at = func.now() if hasattr(func, 'now') else None
    
    db.commit()
    db.refresh(document)
    
    return DocumentResponse(
        id=document.id,
        project_id=document.project_id,
        doc_type=document.doc_type,
        title=document.title,
        content=document.content,
        version=document.version,
        is_validated=document.is_validated,
        created_at=document.created_at,
        updated_at=document.updated_at
    )