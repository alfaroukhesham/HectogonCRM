export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  role?: 'admin' | 'editor' | 'viewer';  // Made optional since backend doesn't provide this
  is_active: boolean;
  is_verified: boolean;
  tenant_id?: string;
  auth_methods: ('password' | 'oauth')[];
  oauth_providers: ('google' | 'facebook' | 'twitter')[];
  created_at: string;
  last_login?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export type OAuthProvider = 'google' | 'facebook' | 'twitter';

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  error: string | null;
}

// Password authentication types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
  role?: 'admin' | 'editor' | 'viewer';
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordResetConfirm {
  token: string;
  new_password: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

export interface EmailVerificationRequest {
  email: string;
}

export interface EmailVerificationConfirm {
  token: string;
}

// API Response types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
}

export interface AuthError {
  message: string;
  field?: string;
}

// OAuth provider info
export interface OAuthProviderInfo {
  name: string;
  display_name: string;
  icon: string;
}

export interface LoginResponse {
  user: User;
  tokens: AuthTokens;
} 
 
 