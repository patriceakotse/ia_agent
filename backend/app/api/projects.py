from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.database import get_db
from app.models.models import Project, Document, Session as ProjectSession, User, ProjectStatus, DocumentType
from app.schemas.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetail,
    DocumentResponse, DocumentUpdate, SessionResponse, SessionUpdate,
    AnalysisRequest, AnalysisResponse
)
from app.services.auth_service import get_current_user
from app.agents.document_generator import generate_all_documents, get_document_title
from app.services.openhands_service import launch_openhands_for_project

router = APIRouter(prefix="/projects", tags=["Projects"])


# ==================== PROJECTS ====================

@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste tous les projets de l'utilisateur."""
    query = db.query(Project).filter(Project.owner_id == current_user.id)
    
    if status:
        query = query.filter(Project.status == status)
    
    if search:
        query = query.filter(Project.name.ilike(f"%{search}%"))
    
    projects = query.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()
    
    # Ajouter des métadonnées
    result = []
    for project in projects:
        docs_count = db.query(Document).filter(Document.project_id == project.id).count()
        has_session = db.query(ProjectSession).filter(
            ProjectSession.project_id == project.id,
            ProjectSession.status == "running"
        ).first() is not None
        
        project_dict = {
            "id": project.id,
            "name": project.name,
            "client": project.client,
            "description": project.description,
            "owner_id": project.owner_id,
            "status": project.status,
            "meeting_notes": project.meeting_notes,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "documents_count": docs_count,
            "has_active_session": has_session
        }
        result.append(ProjectResponse(**project_dict))
    
    return result


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crée un nouveau projet."""
    project = Project(
        name=project_data.name,
        client=project_data.client,
        description=project_data.description,
        meeting_notes=project_data.meeting_notes,
        owner_id=current_user.id,
        status=ProjectStatus.DRAFT.value
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        client=project.client,
        description=project.description,
        owner_id=project.owner_id,
        status=project.status,
        meeting_notes=project.meeting_notes,
        created_at=project.created_at,
        updated_at=project.updated_at,
        documents_count=0,
        has_active_session=False
    )


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère les détails d'un projet."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    # Récupérer les documents
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    document_responses = [
        DocumentResponse(
            id=doc.id,
            project_id=doc.project_id,
            doc_type=doc.doc_type,
            title=doc.title,
            content=doc.content,
            version=doc.version,
            is_validated=doc.is_validated,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        for doc in documents
    ]
    
    # Récupérer les sessions
    sessions = db.query(ProjectSession).filter(ProjectSession.project_id == project_id).all()
    session_responses = [
        SessionResponse(
            id=s.id,
            project_id=s.project_id,
            status=s.status,
            progress=s.progress,
            current_task=s.current_task,
            openhands_session_id=s.openhands_session_id,
            started_at=s.started_at,
            ended_at=s.ended_at,
            error_message=s.error_message
        )
        for s in sessions
    ]
    
    return ProjectDetail(
        id=project.id,
        name=project.name,
        client=project.client,
        description=project.description,
        owner_id=project.owner_id,
        status=project.status,
        meeting_notes=project.meeting_notes,
        created_at=project.created_at,
        updated_at=project.updated_at,
        documents_count=len(documents),
        has_active_session=any(s.status == "running" for s in sessions),
        documents=document_responses,
        sessions=session_responses
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Met à jour un projet."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        client=project.client,
        description=project.description,
        owner_id=project.owner_id,
        status=project.status,
        meeting_notes=project.meeting_notes,
        created_at=project.created_at,
        updated_at=project.updated_at,
        documents_count=db.query(Document).filter(Document.project_id == project.id).count(),
        has_active_session=False
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Supprime un projet."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    db.delete(project)
    db.commit()


# ==================== DOCUMENTS ====================

@router.get("/{project_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les documents d'un projet."""
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
    
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    return [
        DocumentResponse(
            id=doc.id,
            project_id=doc.project_id,
            doc_type=doc.doc_type,
            title=doc.title,
            content=doc.content,
            version=doc.version,
            is_validated=doc.is_validated,
            created_at=doc.created_at,
            updated_at=doc.updated_at
        )
        for doc in documents
    ]


@router.put("/{project_id}/documents/{doc_type}", response_model=DocumentResponse)
async def update_document(
    project_id: int,
    doc_type: str,
    doc_data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Met à jour un document (édition manuelle)."""
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
    
    # Incrémenter la version si le contenu change
    if doc_data.content and doc_data.content != document.content:
        document.version += 1
    
    update_data = doc_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(document, field, value)
    
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


# ==================== ANALYSIS ====================

@router.post("/{project_id}/analyze", response_model=AnalysisResponse)
async def analyze_project(
    project_id: int,
    analysis_data: Optional[AnalysisRequest] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lance l'analyse IA et la génération des documents."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    # Utiliser les meeting_notes ou ceux fournis
    meeting_notes = analysis_data.meeting_notes if analysis_data else project.meeting_notes
    
    if not meeting_notes or len(meeting_notes) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte-rendu insuffisant pour l'analyse (min 10 caractères)"
        )
    
    # Mettre à jour le statut
    project.meeting_notes = meeting_notes
    project.status = ProjectStatus.ANALYZING.value
    db.commit()
    
    # Lancer la génération en arrière-plan
    try:
        documents = generate_all_documents(meeting_notes)
        
        # Sauvegarder les documents générés
        doc_responses = []
        for doc_type, content in documents.items():
            document = db.query(Document).filter(
                Document.project_id == project_id,
                Document.doc_type == doc_type
            ).first()
            
            if document:
                document.content = content
                document.version += 1
            else:
                document = Document(
                    project_id=project_id,
                    doc_type=doc_type,
                    title=get_document_title(doc_type),
                    content=content,
                    version=1
                )
                db.add(document)
            
            db.commit()
            db.refresh(document)
            
            doc_responses.append(DocumentResponse(
                id=document.id,
                project_id=document.project_id,
                doc_type=document.doc_type,
                title=document.title,
                content=document.content,
                version=document.version,
                is_validated=document.is_validated,
                created_at=document.created_at,
                updated_at=document.updated_at
            ))
        
        # Mettre à jour le statut
        project.status = ProjectStatus.VALIDATING.value
        db.commit()
        
        return AnalysisResponse(
            status="success",
            documents=doc_responses,
            message="Documents générés avec succès"
        )
    
    except Exception as e:
        project.status = ProjectStatus.ERROR.value
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération: {str(e)}"
        )


# ==================== OPENHANDS LAUNCH ====================

@router.post("/{project_id}/launch")
async def launch_openhands(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lance OpenHands avec les documents validés."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    # Vérifier qu'il y a des documents validés
    validated_docs = db.query(Document).filter(
        Document.project_id == project_id,
        Document.is_validated == True
    ).all()
    
    if not validated_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Aucun document validé. Validez au moins un document avant de lancer."
        )
    
    # Préparer les documents pour OpenHands
    documents_dict = {doc.doc_type: doc.content for doc in validated_docs}
    
    # Créer une session
    session = ProjectSession(
        project_id=project_id,
        status="running",
        progress=0
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # Mettre à jour le statut du projet
    project.status = ProjectStatus.IN_PROGRESS.value
    db.commit()
    
    try:
        # Lancer OpenHands
        result = await launch_openhands_for_project(
            project=project,
            documents=documents_dict,
            on_log=lambda log: _save_log(db, session.id, log)
        )
        
        # Mettre à jour la session
        session.openhands_session_id = result.get("session_id")
        session.current_task = "Initialisation"
        db.commit()
        
        return {
            "session_id": session.id,
            "openhands_session_id": result.get("session_id"),
            "deep_link": result.get("deep_link"),
            "status": "running"
        }
    
    except Exception as e:
        session.status = "failed"
        session.error_message = str(e)
        session.ended_at = func.now() if hasattr(func, 'now') else None
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement: {str(e)}"
        )


def _save_log(db: Session, session_id: int, log: dict):
    """Sauvegarde un log en base."""
    from app.models.models import Log as LogModel
    log_entry = LogModel(
        session_id=session_id,
        level=log.get("level", "INFO"),
        message=log.get("message", str(log))
    )
    db.add(log_entry)
    db.commit()