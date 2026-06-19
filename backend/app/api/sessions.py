from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
import json
import asyncio
from app.models.database import get_db
from app.models.models import Project, Session as ProjectSession, Log, Feedback, User
from app.schemas.schemas import (
    SessionResponse, SessionUpdate, LogResponse, FeedbackCreate, FeedbackResponse
)
from app.services.auth_service import get_current_user
from app.services.openhands_service import openhands_service

router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["Sessions"])


# ==================== SESSIONS ====================

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les sessions d'un projet."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    sessions = db.query(ProjectSession).filter(
        ProjectSession.project_id == project_id
    ).order_by(desc(ProjectSession.started_at)).all()
    
    return [
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


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    project_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère une session spécifique."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    session = db.query(ProjectSession).filter(
        ProjectSession.id == session_id,
        ProjectSession.project_id == project_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session non trouvée"
        )
    
    return SessionResponse(
        id=session.id,
        project_id=session.project_id,
        status=session.status,
        progress=session.progress,
        current_task=session.current_task,
        openhands_session_id=session.openhands_session_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        error_message=session.error_message
    )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(
    project_id: int,
    session_id: int,
    session_data: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Met à jour une session (depuis OpenHands ou manuellement)."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    session = db.query(ProjectSession).filter(
        ProjectSession.id == session_id,
        ProjectSession.project_id == project_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session non trouvée"
        )
    
    update_data = session_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)
    
    return SessionResponse(
        id=session.id,
        project_id=session.project_id,
        status=session.status,
        progress=session.progress,
        current_task=session.current_task,
        openhands_session_id=session.openhands_session_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        error_message=session.error_message
    )


@router.post("/{session_id}/stop")
async def stop_session(
    project_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Arrête une session en cours."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    session = db.query(ProjectSession).filter(
        ProjectSession.id == session_id,
        ProjectSession.project_id == project_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session non trouvée"
        )
    
    if session.openhands_session_id:
        await openhands_service.stop_session(session.openhands_session_id)
    
    session.status = "completed"
    session.ended_at = db.query(ProjectSession).scalar(
        db.query(ProjectSession.ended_at)
    )
    db.commit()
    
    return {"message": "Session arrêtée"}


# ==================== LOGS ====================

@router.get("/{session_id}/logs", response_model=List[LogResponse])
async def list_logs(
    project_id: int,
    session_id: int,
    skip: int = 0,
    limit: int = 100,
    level: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les logs d'une session."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    query = db.query(Log).filter(Log.session_id == session_id)
    
    if level:
        query = query.filter(Log.level == level)
    
    logs = query.order_by(Log.timestamp.asc()).offset(skip).limit(limit).all()
    
    return [
        LogResponse(
            id=log.id,
            session_id=log.session_id,
            level=log.level,
            message=log.message,
            timestamp=log.timestamp
        )
        for log in logs
    ]


# ==================== FEEDBACK ====================

@router.post("/{session_id}/feedback", response_model=FeedbackResponse)
async def send_feedback(
    project_id: int,
    session_id: int,
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Envoie un feedback à la session OpenHands."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    session = db.query(ProjectSession).filter(
        ProjectSession.id == session_id,
        ProjectSession.project_id == project_id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session non trouvée"
        )
    
    # Sauvegarder le feedback
    feedback = Feedback(
        session_id=session_id,
        content=feedback_data.content,
        is_from_user=True
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    
    # Envoyer à OpenHands si une session est active
    if session.openhands_session_id and session.status == "running":
        try:
            await openhands_service.send_feedback(
                session.openhands_session_id,
                feedback_data.content
            )
        except Exception as e:
            # On ne bloque pas si l'envoi échoue
            print(f"Erreur lors de l'envoi du feedback à OpenHands: {e}")
    
    return FeedbackResponse(
        id=feedback.id,
        session_id=feedback.session_id,
        content=feedback.content,
        is_from_user=feedback.is_from_user,
        created_at=feedback.created_at
    )


@router.get("/{session_id}/feedbacks", response_model=List[FeedbackResponse])
async def list_feedbacks(
    project_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les feedbacks d'une session."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Projet non trouvé"
        )
    
    feedbacks = db.query(Feedback).filter(
        Feedback.session_id == session_id
    ).order_by(Feedback.created_at.asc()).all()
    
    return [
        FeedbackResponse(
            id=f.id,
            session_id=f.session_id,
            content=f.content,
            is_from_user=f.is_from_user,
            created_at=f.created_at
        )
        for f in feedbacks
    ]