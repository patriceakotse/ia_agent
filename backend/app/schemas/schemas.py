from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============ Enums ============
class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    VALIDATING = "validating"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"


class DocumentType(str, Enum):
    README = "readme"
    SPECS = "specs"
    DB_SCHEMA = "db_schema"
    TASKS = "tasks"
    MARKETING = "marketing"
    WORKFLOW = "workflow"


class SessionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ============ User Schemas ============
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Auth Schemas ============
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ============ Project Schemas ============
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    client: Optional[str] = None
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    meeting_notes: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    client: Optional[str] = None
    description: Optional[str] = None
    meeting_notes: Optional[str] = None
    status: Optional[ProjectStatus] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    status: str
    meeting_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    documents_count: int = 0
    has_active_session: bool = False

    class Config:
        from_attributes = True


class ProjectDetail(ProjectResponse):
    documents: List["DocumentResponse"] = []
    sessions: List["SessionResponse"] = []


# ============ Document Schemas ============
class DocumentBase(BaseModel):
    doc_type: DocumentType
    title: str


class DocumentCreate(DocumentBase):
    project_id: int
    content: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_validated: Optional[bool] = None


class DocumentResponse(DocumentBase):
    id: int
    project_id: int
    content: Optional[str] = None
    version: int
    is_validated: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============ Session Schemas ============
class SessionBase(BaseModel):
    project_id: int


class SessionCreate(SessionBase):
    pass


class SessionResponse(BaseModel):
    id: int
    project_id: int
    status: str
    progress: int
    current_task: Optional[str] = None
    openhands_session_id: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class SessionUpdate(BaseModel):
    status: Optional[SessionStatus] = None
    progress: Optional[int] = None
    current_task: Optional[str] = None
    error_message: Optional[str] = None


# ============ Log Schemas ============
class LogResponse(BaseModel):
    id: int
    session_id: int
    level: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


# ============ Feedback Schemas ============
class FeedbackCreate(BaseModel):
    content: str = Field(..., min_length=1)


class FeedbackResponse(BaseModel):
    id: int
    session_id: int
    content: str
    is_from_user: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Analysis Schemas ============
class AnalysisRequest(BaseModel):
    meeting_notes: str = Field(..., min_length=10)


class AnalysisResponse(BaseModel):
    status: str
    documents: List[DocumentResponse]
    message: str


# ============ WebSocket Messages ============
class WSMessageType(str, Enum):
    LOG = "log"
    PROGRESS = "progress"
    STATUS = "status"
    ERROR = "error"
    COMPLETED = "completed"


class WSMessage(BaseModel):
    type: WSMessageType
    data: dict


# Forward references
ProjectDetail.model_rebuild()