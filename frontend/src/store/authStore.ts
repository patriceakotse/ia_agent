import { create } from 'zustand';
import type { User } from '../types';
import { authApi, setTokens, clearTokens, isAuthenticated } from '../services/api';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  
  // Actions
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (username, password) => {
    const response = await authApi.login(username, password);
    setTokens(response.data);
    const userResponse = await authApi.getMe();
    set({ user: userResponse.data, isAuthenticated: true });
  },

  register: async (email, username, password, fullName) => {
    await authApi.register({ email, username, password, full_name: fullName });
    // Auto-login après inscription
    await authApi.login(username, password).then((response) => {
      setTokens(response.data);
    });
    const userResponse = await authApi.getMe();
    set({ user: userResponse.data, isAuthenticated: true });
  },

  logout: () => {
    clearTokens();
    set({ user: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    if (!isAuthenticated()) {
      set({ isLoading: false, isAuthenticated: false });
      return;
    }
    
    try {
      const response = await authApi.getMe();
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch {
      clearTokens();
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },
}));