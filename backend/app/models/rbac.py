from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship
from app.models.database import Base
import enum


class Role(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class Team(Base):
    """Équipe/organisation pour le multi-tenant."""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(String(50), default="free")  # free, pro, enterprise
    created_at = Column(Integer)  # timestamp
    updated_at = Column(Integer)

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """Membre d'une équipe avec rôle."""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default=Role.VIEWER.value)
    invited_by_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(Integer)  # timestamp

    team = relationship("Team", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])


class GitConnection(Base):
    """Connexion GitHub/GitLab pour un projet."""
    __tablename__ = "git_connections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    provider = Column(String(20), nullable=False)  # github, gitlab
    owner = Column(String(255), nullable=False)
    repo = Column(String(255), nullable=False)
    access_token_encrypted = Column(String(500))  # Chiffré
    default_branch = Column(String(100), default="main")
    created_at = Column(Integer)
    updated_at = Column(Integer)

    project = relationship("Project")


# Permissions par rôle
ROLE_PERMISSIONS = {
    Role.OWNER: {
        "project:read": True,
        "project:write": True,
        "project:delete": True,
        "project:manage_members": True,
        "document:read": True,
        "document:write": True,
        "document:validate": True,
        "session:read": True,
        "session:control": True,
        "session:feedback": True,
        "git:read": True,
        "git:write": True,
        "settings:read": True,
        "settings:write": True,
    },
    Role.ADMIN: {
        "project:read": True,
        "project:write": True,
        "project:delete": False,
        "project:manage_members": True,
        "document:read": True,
        "document:write": True,
        "document:validate": True,
        "session:read": True,
        "session:control": True,
        "session:feedback": True,
        "git:read": True,
        "git:write": True,
        "settings:read": True,
        "settings:write": False,
    },
    Role.EDITOR: {
        "project:read": True,
        "project:write": True,
        "project:delete": False,
        "project:manage_members": False,
        "document:read": True,
        "document:write": True,
        "document:validate": True,
        "session:read": True,
        "session:control": False,
        "session:feedback": True,
        "git:read": True,
        "git:write": False,
        "settings:read": True,
        "settings:write": False,
    },
    Role.VIEWER: {
        "project:read": True,
        "project:write": False,
        "project:delete": False,
        "project:manage_members": False,
        "document:read": True,
        "document:write": False,
        "document:validate": False,
        "session:read": True,
        "session:control": False,
        "session:feedback": False,
        "git:read": True,
        "git:write": False,
        "settings:read": False,
        "settings:write": False,
    },
}


def has_permission(role: Role, permission: str) -> bool:
    """Vérifie si un rôle a une permission spécifique."""
    return ROLE_PERMISSIONS.get(role, {}).get(permission, False)


def get_user_role_in_project(db, user_id: int, project_id: int) -> Role:
    """Récupère le rôle d'un utilisateur dans un projet."""
    from app.models.models import Project
    
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        return None
    
    # Le propriétaire du projet a le rôle owner
    if project.owner_id == user_id:
        return Role.OWNER
    
    # Vérifier si l'utilisateur est membre de l'équipe du projet
    if project.team_id:
        member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == user_id
        ).first()
        
        if member:
            return Role(member.role)
    
    return None