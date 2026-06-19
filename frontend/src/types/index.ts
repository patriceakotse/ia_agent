// Types pour le frontend

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export type ProjectStatus = 'draft' | 'analyzing' | 'validating' | 'in_progress' | 'completed' | 'error';
export type DocumentType = 'readme' | 'specs' | 'db_schema' | 'tasks' | 'marketing' | 'workflow';
export type SessionStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface Project {
  id: number;
  name: string;
  client?: string;
  description?: string;
  owner_id: number;
  status: ProjectStatus;
  meeting_notes?: string;
  created_at: string;
  updated_at?: string;
  documents_count: number;
  has_active_session: boolean;
}

export interface ProjectDetail extends Project {
  documents: Document[];
  sessions: Session[];
}

export interface Document {
  id: number;
  project_id: number;
  doc_type: DocumentType;
  title: string;
  content?: string;
  version: number;
  is_validated: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Session {
  id: number;
  project_id: number;
  status: SessionStatus;
  progress: number;
  current_task?: string;
  openhands_session_id?: string;
  started_at: string;
  ended_at?: string;
  error_message?: string;
}

export interface Log {
  id: number;
  session_id: number;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR';
  message: string;
  timestamp: string;
}

export interface Feedback {
  id: number;
  session_id: number;
  content: string;
  is_from_user: boolean;
  created_at: string;
}

export interface AnalysisResponse {
  status: string;
  documents: Document[];
  message: string;
}

export interface LaunchResponse {
  session_id: number;
  openhands_session_id: string;
  deep_link: string;
  status: string;
}

export interface CreateProjectData {
  name: string;
  client?: string;
  description?: string;
  meeting_notes?: string;
}

export interface UpdateProjectData {
  name?: string;
  client?: string;
  description?: string;
  meeting_notes?: string;
  status?: ProjectStatus;
}

export interface UpdateDocumentData {
  title?: string;
  content?: string;
  is_validated?: boolean;
}

export interface WSMessage {
  type: 'log' | 'progress' | 'status' | 'error' | 'completed';
  data: Record<string, unknown>;
}