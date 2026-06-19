from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.models.database import get_db
from app.models.models import Project, User
from app.models.rbac import GitConnection, has_permission, Role, get_user_role_in_project
from app.services.git_integration import git_service, GitProvider
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/projects/{project_id}/git", tags=["Git Integration"])


# ==================== SCHEMAS ====================

class GitConnectionRequest(BaseModel):
    provider: str  # github, gitlab
    owner: str
    repo: str
    access_token: str
    default_branch: Optional[str] = "main"


class GitConnectionResponse(BaseModel):
    id: int
    provider: str
    owner: str
    repo: str
    default_branch: str


class BranchResponse(BaseModel):
    name: str


class PRCreateRequest(BaseModel):
    title: str
    description: str
    source_branch: str
    target_branch: Optional[str] = "main"


class PRResponse(BaseModel):
    number: int
    title: str
    description: str
    state: str
    url: str
    branch: str


class CreateBranchRequest(BaseModel):
    name: str
    from_branch: Optional[str] = "main"


# ==================== HELPER ====================

def check_git_permission(user_id: int, project_id: int, permission: str, db: Session) -> bool:
    """Vérifie si l'utilisateur a la permission Git spécifiée."""
    role = get_user_role_in_project(db, user_id, project_id)
    if not role:
        return False
    return has_permission(role, permission)


# ==================== ROUTES ====================

@router.get("/repos", response_model=List[dict])
async def list_connected_repos(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les repositories Git connectés à un projet."""
    if not check_git_permission(current_user.id, project_id, "git:read", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    
    connections = db.query(GitConnection).filter(
        GitConnection.project_id == project_id
    ).all()
    
    return [
        {
            "id": c.id,
            "provider": c.provider,
            "owner": c.owner,
            "repo": c.repo,
            "default_branch": c.default_branch
        }
        for c in connections
    ]


@router.post("/connect", response_model=GitConnectionResponse)
async def connect_repository(
    project_id: int,
    connection_data: GitConnectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Connecte un repository GitHub/GitLab au projet."""
    if not check_git_permission(current_user.id, project_id, "git:write", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    
    # Vérifier que le provider est valide
    if connection_data.provider not in ["github", "gitlab"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider non supporté"
        )
    
    # Vérifier si déjà connecté
    existing = db.query(GitConnection).filter(
        GitConnection.project_id == project_id,
        GitConnection.provider == connection_data.provider,
        GitConnection.owner == connection_data.owner,
        GitConnection.repo == connection_data.repo
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce repository est déjà connecté"
        )
    
    connection = GitConnection(
        project_id=project_id,
        provider=connection_data.provider,
        owner=connection_data.owner,
        repo=connection_data.repo,
        access_token_encrypted=connection_data.access_token,  # À chiffrer en prod
        default_branch=connection_data.default_branch
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    
    return GitConnectionResponse(
        id=connection.id,
        provider=connection.provider,
        owner=connection.owner,
        repo=connection.repo,
        default_branch=connection.default_branch
    )


@router.delete("/disconnect/{connection_id}")
async def disconnect_repository(
    project_id: int,
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Déconnecte un repository."""
    if not check_git_permission(current_user.id, project_id, "git:write", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    
    connection = db.query(GitConnection).filter(
        GitConnection.id == connection_id,
        GitConnection.project_id == project_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connexion non trouvée")
    
    db.delete(connection)
    db.commit()
    
    return {"message": "Repository déconnecté"}


@router.get("/branches", response_model=List[str])
async def list_branches(
    project_id: int,
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les branches d'un repository connecté."""
    if not check_git_permission(current_user.id, project_id, "git:read", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    
    connection = db.query(GitConnection).filter(
        GitConnection.id == connection_id,
        GitConnection.project_id == project_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connexion non trouvée")
    
    try:
        if connection.provider == "github":
            branches = await git_service.github_get_branches(
                connection.access_token_encrypted,
                connection.owner,
                connection.repo
            )
        else:
            # GitLab - à implémenter
            branches = []
        
        return branches
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des branches: {str(e)}"
        )


@router.post("/branches", status_code=status.HTTP_201_CREATED)
async def create_branch(
    project_id: int,
    connection_id: int,
    branch_data: CreateBranchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crée une nouvelle branche."""
    if not check_git_permission(current_user.id, project_id, "git:write", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    
    connection = db.query(GitConnection).filter(
        GitConnection.id == connection_id,
        GitConnection.project_id == project_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connexion non trouvée")
    
    try:
        if connection.provider == "github":
            await git_service.github_create_branch(
                connection.access_token_encrypted,
                connection.owner,
                connection.repo,
                branch_data.name,
                branch_data.from_branch
            )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider non supporté")
        
        return {"message": "Branche créée", "branch": branch_data.name}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la branche: {str(e)}"
        )


@router.get("/pull-requests", response_model=List[PRResponse])
async def list_pull_requests(
    project_id: int,
    connection_id: int,
    state: str = "open",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les Pull Requests."""
    if not check_git_permission(current_user.id, project_id, "git:read", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    
    connection = db.query(GitConnection).filter(
        GitConnection.id == connection_id,
        GitConnection.project_id == project_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connexion non trouvée")
    
    try:
        if connection.provider == "github":
            prs = await git_service.github_list_prs(
                connection.access_token_encrypted,
                connection.owner,
                connection.repo,
                state
            )
            return [
                PRResponse(
                    number=pr.number,
                    title=pr.title,
                    description=pr.description,
                    state=pr.state,
                    url=pr.url,
                    branch=pr.branch
                )
                for pr in prs
            ]
        else:
            return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )


@router.post("/pull-requests", response_model=PRResponse)
async def create_pull_request(
    project_id: int,
    connection_id: int,
    pr_data: PRCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crée une Pull Request."""
    if not check_git_permission(current_user.id, project_id, "git:write", db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")
    
    connection = db.query(GitConnection).filter(
        GitConnection.id == connection_id,
        GitConnection.project_id == project_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connexion non trouvée")
    
    try:
        if connection.provider == "github":
            pr = await git_service.github_create_pr(
                connection.access_token_encrypted,
                connection.owner,
                connection.repo,
                pr_data.title,
                pr_data.description,
                pr_data.source_branch,
                pr_data.target_branch
            )
            return PRResponse(
                number=pr.number,
                title=pr.title,
                description=pr.description,
                state=pr.state,
                url=pr.url,
                branch=pr.branch
            )
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider non supporté")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur: {str(e)}"
        )