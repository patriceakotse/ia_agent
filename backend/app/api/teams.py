from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.models.database import get_db
from app.models.models import User
from app.models.rbac import Team, TeamMember, Role, has_permission, get_user_role_in_project
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/teams", tags=["Teams"])


# ==================== SCHEMAS ====================

class TeamCreate(BaseModel):
    name: str
    slug: Optional[str] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    slug: str
    plan: str
    member_count: int = 0


class TeamMemberResponse(BaseModel):
    id: int
    user_id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    joined_at: Optional[int]


class InviteMemberRequest(BaseModel):
    email: str
    role: str = "viewer"


class UpdateMemberRoleRequest(BaseModel):
    role: str


# ==================== ROUTES ====================

@router.get("", response_model=List[TeamResponse])
async def list_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les équipes dont l'utilisateur est membre."""
    memberships = db.query(TeamMember).filter(
        TeamMember.user_id == current_user.id
    ).all()
    
    teams = []
    for membership in memberships:
        team = db.query(Team).filter(Team.id == membership.team_id).first()
        if team:
            member_count = db.query(TeamMember).filter(
                TeamMember.team_id == team.id
            ).count()
            teams.append(TeamResponse(
                id=team.id,
                name=team.name,
                slug=team.slug,
                plan=team.plan,
                member_count=member_count
            ))
    
    return teams


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crée une nouvelle équipe."""
    import re
    
    # Générer le slug si non fourni
    slug = team_data.slug or re.sub(r'[^a-z0-9]+', '-', team_data.name.lower())
    
    # Vérifier l'unicité du slug
    existing = db.query(Team).filter(Team.slug == slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'équipe est déjà pris"
        )
    
    import time
    team = Team(
        name=team_data.name,
        slug=slug,
        plan="free",
        created_at=int(time.time())
    )
    db.add(team)
    db.flush()
    
    # Ajouter le créateur comme owner
    membership = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=Role.OWNER.value,
        joined_at=int(time.time())
    )
    db.add(membership)
    db.commit()
    db.refresh(team)
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        plan=team.plan,
        member_count=1
    )


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère les détails d'une équipe."""
    # Vérifier l'accès
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette équipe"
        )
    
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Équipe non trouvée"
        )
    
    member_count = db.query(TeamMember).filter(
        TeamMember.team_id == team.id
    ).count()
    
    return TeamResponse(
        id=team.id,
        name=team.name,
        slug=team.slug,
        plan=team.plan,
        member_count=member_count
    )


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def list_team_members(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Liste les membres d'une équipe."""
    # Vérifier l'accès
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas accès à cette équipe"
        )
    
    members = db.query(TeamMember).filter(
        TeamMember.team_id == team_id
    ).all()
    
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        if user:
            result.append(TeamMemberResponse(
                id=m.id,
                user_id=m.user_id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=m.role,
                joined_at=m.joined_at
            ))
    
    return result


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED)
async def invite_member(
    team_id: int,
    invite_data: InviteMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Invite un membre dans l'équipe."""
    # Vérifier les permissions
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership or not has_permission(Role(membership.role), "project:manage_members"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission d'inviter des membres"
        )
    
    # Trouver l'utilisateur par email
    user = db.query(User).filter(User.email == invite_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Vérifier si déjà membre
    existing = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet utilisateur est déjà membre de l'équipe"
        )
    
    import time
    new_membership = TeamMember(
        team_id=team_id,
        user_id=user.id,
        role=invite_data.role,
        invited_by_id=current_user.id,
        joined_at=int(time.time())
    )
    db.add(new_membership)
    db.commit()
    
    return {"message": "Membre invité avec succès"}


@router.put("/{team_id}/members/{user_id}")
async def update_member_role(
    team_id: int,
    user_id: int,
    role_data: UpdateMemberRoleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modifie le rôle d'un membre."""
    # Vérifier les permissions
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership or not has_permission(Role(membership.role), "project:manage_members"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission de modifier les rôles"
        )
    
    # Ne pas permettre de modifier le owner
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vous ne pouvez pas modifier votre propre rôle"
        )
    
    target_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membre non trouvé"
        )
    
    # Ne pas permettre de donner un rôle owner
    if role_data.role == Role.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'attribuer le rôle Owner"
        )
    
    target_membership.role = role_data.role
    db.commit()
    
    return {"message": "Rôle mis à jour"}


@router.delete("/{team_id}/members/{user_id}")
async def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retire un membre de l'équipe."""
    # Vérifier les permissions
    membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == current_user.id
    ).first()
    
    if not membership or not has_permission(Role(membership.role), "project:manage_members"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'avez pas la permission de retirer des membres"
        )
    
    # Ne pas permettre de se retirer soi-même si on est owner
    if user_id == current_user.id and membership.role == Role.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le Owner ne peut pas se retirer lui-même"
        )
    
    target_membership = db.query(TeamMember).filter(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id
    ).first()
    
    if not target_membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Membre non trouvé"
        )
    
    db.delete(target_membership)
    db.commit()
    
    return {"message": "Membre retiré"}