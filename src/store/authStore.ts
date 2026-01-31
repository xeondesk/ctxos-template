import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { AuthState, UserInfo, LoginRequest } from 'types';
import { apiClient } from 'api';

interface AuthStore extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: (refreshToken: string) => Promise<void>;
  verifyToken: () => Promise<boolean>;
  setUser: (user: UserInfo) => void;
  clearError: () => void;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      user: null,
      token: null,
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials: LoginRequest) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await apiClient.login(credentials);
          
          set({
            isAuthenticated: true,
            user: response.user_info,
            token: response.access_token,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            isLoading: false,
            error: error.response?.data?.detail || 'Login failed',
          });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        
        try {
          await apiClient.logout();
        } catch (error) {
          // Ignore logout errors
        } finally {
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            isLoading: false,
            error: null,
          });
        }
      },

      refreshToken: async (refreshToken: string) => {
        try {
          const response = await apiClient.refreshToken(refreshToken);
          
          set({
            token: response.access_token,
            error: null,
          });
        } catch (error: any) {
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            error: 'Token refresh failed',
          });
          throw error;
        }
      },

      verifyToken: async (): Promise<boolean> => {
        const { token } = get();
        
        if (!token) {
          return false;
        }

        try {
          const response = await apiClient.verifyToken();
          return response.valid;
        } catch (error) {
          set({
            isAuthenticated: false,
            user: null,
            token: null,
            error: 'Token verification failed',
          });
          return false;
        }
      },

      setUser: (user: UserInfo) => {
        set({ user });
      },

      clearError: () => {
        set({ error: null });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        isAuthenticated: state.isAuthenticated,
        user: state.user,
        token: state.token,
      }),
    }
  )
);

// Selectors
export const useAuth = () => useAuthStore((state) => ({
  isAuthenticated: state.isAuthenticated,
  user: state.user,
  token: state.token,
  isLoading: state.isLoading,
  error: state.error,
}));

export const useAuthActions = () => useAuthStore((state) => ({
  login: state.login,
  logout: state.logout,
  refreshToken: state.refreshToken,
  verifyToken: state.verifyToken,
  setUser: state.setUser,
  clearError: state.clearError,
}));

// Helper hooks
export const useIsAuthenticated = () => useAuthStore((state) => state.isAuthenticated);
export const useCurrentUser = () => useAuthStore((state) => state.user);
export const useAuthToken = () => useAuthStore((state) => state.token);
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);
export const useAuthError = () => useAuthStore((state) => state.error);
