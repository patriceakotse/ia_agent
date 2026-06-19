from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from app.models.database import get_db
from app.models.models import Project, Session as ProjectSession, Log, User
from app.services.openhands_monitor import get_monitor, analyze_openhands_log
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/projects/{project_id}/sessions/{session_id}/alerts", tags=["Alerts"])


# ==================== SCHEMAS ====================

class AlertResponse:
    def __init__(self, severity: str, type: str, message: str, details: dict, timestamp: datetime):
        self.severity = severity
        self.type = type
        self.message = message
        self.details = details
        self.timestamp = timestamp
    
    def to_dict(self):
        return {
            "severity": self.severity,
            "type": self.type,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


# ==================== ROUTES ====================

@router.get("", response_model=List[dict])
async def get_session_alerts(
    project_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère les alertes d'une session."""
    # Vérifier l'accès
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    
    session = db.query(ProjectSession).filter(
        ProjectSession.id == session_id,
        ProjectSession.project_id == project_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session non trouvée")
    
    # Récupérer le monitor
    monitor = get_monitor(session_id)
    summary = monitor.get_summary()
    
    # Convertir les alertes en format de réponse
    alerts = []
    for alert in monitor.alerts[-20:]:  # 20 dernières alertes
        alerts.append(alert.to_dict())
    
    return {
        "summary": summary,
        "alerts": alerts
    }


@router.post("/analyze-log")
async def analyze_log(
    project_id: int,
    session_id: int,
    log_message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyse un log et génère des alertes si nécessaire."""
    # Vérifier l'accès
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    
    session = db.query(ProjectSession).filter(
        ProjectSession.id == session_id,
        ProjectSession.project_id == project_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session non trouvée")
    
    # Analyser le log
    alerts = analyze_openhands_log(session_id, log_message)
    
    return {
        "analyzed": log_message[:100],
        "alerts_count": len(alerts),
        "alerts": [a.to_dict() for a in alerts]
    }


@router.post("/reset")
async def reset_alerts(
    project_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Réinitialise les alertes d'une session."""
    # Vérifier l'accès
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    
    # Récupérer et réinitialiser le monitor
    monitor = get_monitor(session_id)
    monitor.reset()
    
    return {"message": "Alertes réinitialisées"}


@router.get("/stats")
async def get_alert_stats(
    project_id: int,
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère les statistiques d'alertes."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projet non trouvé")
    
    session = db.query(ProjectSession).filter(
        ProjectSession.id == session_id,
        ProjectSession.project_id == project_id
    ).first()
    
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session non trouvé")
    
    monitor = get_monitor(session_id)
    summary = monitor.get_summary()
    
    # Analyser les logs de la session pour des stats supplémentaires
    logs = db.query(Log).filter(Log.session_id == session_id).all()
    
    error_count = sum(1 for log in logs if log.level == "ERROR")
    warning_count = sum(1 for log in logs if log.level == "WARNING")
    
    return {
        **summary,
        "logs_analyzed": len(logs),
        "total_errors": error_count,
        "total_warnings": warning_count
    }