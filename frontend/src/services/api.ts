import axios from 'axios';
import type {
  User, Token, Project, ProjectDetail, Document,
  Session, Log, Feedback, AnalysisResponse, LaunchResponse,
  CreateProjectData, UpdateProjectData, UpdateDocumentData
} from '../types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteur pour ajouter le token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Intercepteur pour gérer les erreurs d'auth
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Tenter de refresh le token
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, null, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          });
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          // Retry la requête originale
          error.config.headers.Authorization = `Bearer ${access_token}`;
          return api(error.config);
        } catch {
          // Refresh échoué, déconnexion
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ==================== AUTH ====================

export const authApi = {
  register: (data: { email: string; username: string; password: string; full_name?: string }) =>
    api.post<User>('/auth/register', data),

  login: (username: string, password: string) =>
    api.post<Token>('/auth/login', { username, password }, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),

  refresh: (refreshToken: string) =>
    api.post<Token>('/auth/refresh', null, {
      headers: { Authorization: `Bearer ${refreshToken}` },
    }),

  getMe: () =>
    api.get<User>('/auth/me'),

  updateMe: (data: Partial<User>) =>
    api.put<User>('/auth/me', data),
};

// ==================== PROJECTS ====================

export const projectsApi = {
  list: (params?: { skip?: number; limit?: number; status?: string; search?: string }) =>
    api.get<Project[]>('/projects', { params }),

  create: (data: CreateProjectData) =>
    api.post<Project>('/projects', data),

  get: (projectId: number) =>
    api.get<ProjectDetail>(`/projects/${projectId}`),

  update: (projectId: number, data: UpdateProjectData) =>
    api.put<Project>(`/projects/${projectId}`, data),

  delete: (projectId: number) =>
    api.delete(`/projects/${projectId}`),

  analyze: (projectId: number, meetingNotes?: string) =>
    api.post<AnalysisResponse>(`/projects/${projectId}/analyze`, meetingNotes ? { meeting_notes: meetingNotes } : {}),

  launch: (projectId: number) =>
    api.post<LaunchResponse>(`/projects/${projectId}/launch`),
};

// ==================== DOCUMENTS ====================

export const documentsApi = {
  list: (projectId: number) =>
    api.get<Document[]>(`/projects/${projectId}/documents`),

  update: (projectId: number, docType: string, data: UpdateDocumentData) =>
    api.put<Document>(`/projects/${projectId}/documents/${docType}`, data),
};

// ==================== SESSIONS ====================

export const sessionsApi = {
  list: (projectId: number) =>
    api.get<Session[]>(`/projects/${projectId}/sessions`),

  get: (projectId: number, sessionId: number) =>
    api.get<Session>(`/projects/${projectId}/sessions/${sessionId}`),

  update: (projectId: number, sessionId: number, data: Partial<Session>) =>
    api.put<Session>(`/projects/${projectId}/sessions/${sessionId}`, data),

  stop: (projectId: number, sessionId: number) =>
    api.post(`/projects/${projectId}/sessions/${sessionId}/stop`),

  getLogs: (projectId: number, sessionId: number, params?: { skip?: number; limit?: number; level?: string }) =>
    api.get<Log[]>(`/projects/${projectId}/sessions/${sessionId}/logs`, { params }),

  sendFeedback: (projectId: number, sessionId: number, content: string) =>
    api.post<Feedback>(`/projects/${projectId}/sessions/${sessionId}/feedback`, { content }),

  listFeedbacks: (projectId: number, sessionId: number) =>
    api.get<Feedback[]>(`/projects/${projectId}/sessions/${sessionId}/feedbacks`),
};

// ==================== UTILS ====================

export const setTokens = (token: Token) => {
  localStorage.setItem('access_token', token.access_token);
  localStorage.setItem('refresh_token', token.refresh_token);
};

export const clearTokens = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

export const isAuthenticated = () => {
  return !!localStorage.getItem('access_token');
};

export default api;