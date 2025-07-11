import React, { createContext, useContext, useEffect, useState, useRef, ReactNode } from 'react';
import { 
  User, 
  AuthTokens, 
  AuthState, 
  LoginCredentials, 
  RegisterData, 
  PasswordResetRequest, 
  PasswordResetConfirm,
  PasswordChange,
  EmailVerificationRequest,
  EmailVerificationConfirm 
} from '../types/auth';
import { api, ApiError } from '../utils/api';

interface AuthContextType extends AuthState {
  // Password authentication
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  logoutAll: () => Promise<void>;
  
  // Password management
  forgotPassword: (data: PasswordResetRequest) => Promise<string>;
  resetPassword: (data: PasswordResetConfirm) => Promise<string>;
  changePassword: (data: PasswordChange) => Promise<string>;
  
  // Email verification
  verifyEmail: (data: EmailVerificationConfirm) => Promise<string>;
  resendVerification: (data: EmailVerificationRequest) => Promise<string>;
  
  // OAuth
  initiateOAuth: (provider: string) => Promise<void>;
  handleOAuthCallback: (accessToken: string, refreshToken: string) => Promise<void>;
  
  // Utility
  refreshTokens: () => Promise<boolean>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    user: null,
    tokens: null,
    isLoading: true,
    isAuthenticated: false,
    error: null,
  });

  const initializingRef = useRef(false);

  // Initialize authentication state
  useEffect(() => {
    if (!initializingRef.current && !state.isAuthenticated) {
      initializingRef.current = true;
      initializeAuth();
    }
  }, []);

  const initializeAuth = async () => {
    try {
      const storedTokens = localStorage.getItem('auth_tokens');
      const storedUser = localStorage.getItem('auth_user');

      if (storedTokens && storedUser) {
        const tokens: AuthTokens = JSON.parse(storedTokens);
        const user: User = JSON.parse(storedUser);

        setState(prev => ({
          ...prev,
          user,
          tokens,
          isAuthenticated: true,
          isLoading: false,
        }));

        // Verify tokens are still valid by fetching user info
        try {
          const currentUser = await api.getCurrentUser();
          setState(prev => ({
            ...prev,
            user: currentUser,
            isLoading: false,
          }));
          localStorage.setItem('auth_user', JSON.stringify(currentUser));
        } catch (error) {
          // Tokens are invalid, clear them
          try {
            await logout();
          } catch (logoutError) {
            console.warn('Failed to logout during token validation:', logoutError);
          }
        }
      } else {
        setState(prev => ({
          ...prev,
          isLoading: false,
        }));
      }
    } catch (error) {
      console.error('Failed to initialize auth:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: 'Failed to initialize authentication',
      }));
    } finally {
      initializingRef.current = false;
    }
  };

  const setError = (error: string | null) => {
    setState(prev => ({ ...prev, error }));
  };

  const clearError = () => {
    setState(prev => ({ ...prev, error: null }));
  };

  const setLoading = (isLoading: boolean) => {
    setState(prev => ({ ...prev, isLoading }));
  };

  // Password authentication
  const login = async (credentials: LoginCredentials) => {
    try {
      setLoading(true);
      clearError();

      const tokens = await api.login(credentials);
      
      // Store tokens BEFORE calling getCurrentUser so the API client can use them
      localStorage.setItem('auth_tokens', JSON.stringify(tokens));
      
      const user = await api.getCurrentUser();

      // Store user info
      localStorage.setItem('auth_user', JSON.stringify(user));

      setState(prev => ({
        ...prev,
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
      }));
    } catch (error) {
      // Clear any partially stored tokens on error
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_user');
      
      const message = error instanceof ApiError 
        ? error.message 
        : 'Login failed. Please try again.';
      
      setState(prev => ({
        ...prev,
        error: message,
        isLoading: false,
      }));
      throw error;
    }
  };

  const register = async (data: RegisterData) => {
    try {
      setLoading(true);
      clearError();

      await api.register(data);

      setState(prev => ({
        ...prev,
        isLoading: false,
      }));

      // Note: User needs to verify email before they can login
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Registration failed. Please try again.';
      
      setState(prev => ({
        ...prev,
        error: message,
        isLoading: false,
      }));
      throw error;
    }
  };

  const logout = async () => {
    try {
      const tokens = state.tokens;
      
      // Clear local state first
      setState({
        user: null,
        tokens: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      });

      // Clear storage
      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_user');

      // Call logout API
      if (tokens?.refresh_token) {
        try {
          await api.logout(tokens.refresh_token);
        } catch (error) {
          console.warn('Logout API call failed:', error);
        }
      }
    } catch (error) {
      console.error('Logout failed:', error);
      // Still clear local state even if API call fails
      setState({
        user: null,
        tokens: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      });

      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_user');
    }
  };

  const logoutAll = async () => {
    try {
      // Call logout all API first
      await api.logoutAll();
    } catch (error) {
      console.warn('Logout all API call failed:', error);
    } finally {
      // Clear local state regardless
      setState({
        user: null,
        tokens: null,
        isLoading: false,
        isAuthenticated: false,
        error: null,
      });

      localStorage.removeItem('auth_tokens');
      localStorage.removeItem('auth_user');
    }
  };

  // Password management
  const forgotPassword = async (data: PasswordResetRequest): Promise<string> => {
    try {
      clearError();
      const response = await api.forgotPassword(data);
      return response.message;
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to send reset email. Please try again.';
      setError(message);
      throw error;
    }
  };

  const resetPassword = async (data: PasswordResetConfirm): Promise<string> => {
    try {
      clearError();
      const response = await api.resetPassword(data);
      return response.message;
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to reset password. Please try again.';
      setError(message);
      throw error;
    }
  };

  const changePassword = async (data: PasswordChange): Promise<string> => {
    try {
      clearError();
      const response = await api.changePassword(data);
      return response.message;
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to change password. Please try again.';
      setError(message);
      throw error;
    }
  };

  // Email verification
  const verifyEmail = async (data: EmailVerificationConfirm): Promise<string> => {
    try {
      clearError();
      const response = await api.verifyEmail(data);
      
      // Refresh user info to update verification status
      if (state.isAuthenticated) {
        const user = await api.getCurrentUser();
        setState(prev => ({ ...prev, user }));
        localStorage.setItem('auth_user', JSON.stringify(user));
      }
      
      return response.message;
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to verify email. Please try again.';
      setError(message);
      throw error;
    }
  };

  const resendVerification = async (data: EmailVerificationRequest): Promise<string> => {
    try {
      clearError();
      const response = await api.resendVerification(data);
      return response.message;
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to resend verification email. Please try again.';
      setError(message);
      throw error;
    }
  };

  // OAuth
  const initiateOAuth = async (provider: string) => {
    try {
      clearError();
      const { authorization_url } = await api.initiateOAuth(provider, window.location.origin);
      window.location.href = authorization_url;
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'Failed to initiate OAuth login. Please try again.';
      setError(message);
      throw error;
    }
  };

  const handleOAuthCallback = async (accessToken: string, refreshToken: string) => {
    try {
      setLoading(true);
      clearError();

      const tokens: AuthTokens = {
        access_token: accessToken,
        refresh_token: refreshToken,
        token_type: 'bearer',
        expires_in: 1800, // 30 minutes
      };

      // Store tokens first
      localStorage.setItem('auth_tokens', JSON.stringify(tokens));

      // Get user info
      const user = await api.getCurrentUser();
      localStorage.setItem('auth_user', JSON.stringify(user));

      setState(prev => ({
        ...prev,
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
      }));
    } catch (error) {
      const message = error instanceof ApiError 
        ? error.message 
        : 'OAuth callback failed. Please try again.';
      
      setState(prev => ({
        ...prev,
        error: message,
        isLoading: false,
      }));
      throw error;
    }
  };

  // Token refresh
  const refreshTokens = async (): Promise<boolean> => {
    try {
      if (!state.tokens?.refresh_token) {
        return false;
      }

      const newTokens = await api.refreshToken(state.tokens.refresh_token);
      if (!newTokens) {
        await logout();
        return false;
      }

      setState(prev => ({
        ...prev,
        tokens: newTokens,
      }));

      return true;
    } catch (error) {
      console.error('Token refresh failed:', error);
      await logout();
      return false;
    }
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    logoutAll,
    forgotPassword,
    resetPassword,
    changePassword,
    verifyEmail,
    resendVerification,
    initiateOAuth,
    handleOAuthCallback,
    refreshTokens,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
} 
