import { 
  Contact, 
  Deal, 
  Activity,
  Organization,
  OrganizationCreateRequest,
  OrganizationUpdateRequest,
  OrganizationMembership,
  Invitation,
  InvitationCreateRequest,
  MembershipRole
} from '../types';
import { AuthStorage } from './auth';
import { 
  User, 
  AuthTokens, 
  LoginCredentials, 
  RegisterData, 
  PasswordResetRequest, 
  PasswordResetConfirm,
  PasswordChange,
  EmailVerificationRequest,
  EmailVerificationConfirm,
  OAuthProviderInfo
} from '../types/auth';

const BACKEND_URL = (import.meta as any).env?.VITE_BACKEND_URL || 'http://localhost:8000';
const BASE_URL = `${BACKEND_URL}/api`;

// Storage abstraction interface
interface StorageAdapter {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

// Default localStorage implementation
class LocalStorageAdapter implements StorageAdapter {
  getItem(key: string): string | null {
    return localStorage.getItem(key);
  }
  
  setItem(key: string, value: string): void {
    localStorage.setItem(key, value);
  }
  
  removeItem(key: string): void {
    localStorage.removeItem(key);
  }
}


class ApiError extends Error {
  constructor(
    public status: number, 
    message: string, 
    public validationErrors?: any[]
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

class ApiClient {
  private baseUrl: string;
  private storage: StorageAdapter;
  private refreshPromise: Promise<AuthTokens | null> | null = null;
  private currentOrganizationId: string | null = null;

  constructor(baseUrl: string = BASE_URL, storage: StorageAdapter = new LocalStorageAdapter()) {
    this.baseUrl = baseUrl;
    this.storage = storage;
    
    // Load current organization from storage
    const orgId = this.storage.getItem('current_organization_id');
    this.currentOrganizationId = orgId;
  }

  setCurrentOrganization(organizationId: string | null): void {
    this.currentOrganizationId = organizationId;
    if (organizationId) {
      this.storage.setItem('current_organization_id', organizationId);
    } else {
      this.storage.removeItem('current_organization_id');
    }
  }

  getCurrentOrganization(): string | null {
    return this.currentOrganizationId;
  }

  private async refreshTokenWithLock(refreshToken: string): Promise<AuthTokens | null> {
    // If refresh is already in progress, wait for it
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    // Start refresh process
    this.refreshPromise = this.refreshToken(refreshToken);
    
    try {
      const result = await this.refreshPromise;
      return result;
    } finally {
      // Clear the promise regardless of success/failure
      this.refreshPromise = null;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    // Get tokens from storage
    const tokens = this.storage.getItem('auth_tokens');
    const authTokens = tokens ? JSON.parse(tokens) : null;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add authorization header if we have an access token
    // Exclude auth endpoints that don't need tokens (login, register, etc) but include /me and other protected auth endpoints
    const authEndpointsThatNeedTokens = ['/auth/me', '/auth/logout', '/auth/logout-all', '/auth/change-password', '/auth/verify-email', '/auth/resend-verification'];
    const isProtectedAuthEndpoint = authEndpointsThatNeedTokens.some(protectedEndpoint => endpoint.includes(protectedEndpoint));
    const isPublicAuthEndpoint = endpoint.includes('/auth/') && !isProtectedAuthEndpoint;
    
    if (authTokens?.access_token && !isPublicAuthEndpoint) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${authTokens.access_token}`,
      };
    }

    // Add organization header if we have a current organization
    if (this.currentOrganizationId && !endpoint.includes('/auth/') && !endpoint.includes('/organizations')) {
      config.headers = {
        ...config.headers,
        'X-Organization-ID': this.currentOrganizationId,
      };
    }

    // Removed debug logging

    try {
      const response = await fetch(url, config);
      
      // Removed debug logging
      
      // Handle 401 errors - try to refresh token
      if (response.status === 401 && authTokens?.refresh_token && !endpoint.includes('/auth/refresh')) {
        const refreshed = await this.refreshTokenWithLock(authTokens.refresh_token);
        if (refreshed) {
          // Retry the original request with new token
          config.headers = {
            ...config.headers,
            Authorization: `Bearer ${refreshed.access_token}`,
          };
          const retryResponse = await fetch(url, config);
          if (!retryResponse.ok) {
            this.handleErrorResponse(retryResponse);
          }
          return retryResponse.json();
        }
      }

      if (!response.ok) {
        await this.handleErrorResponse(response);
      }

      return response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(0, 'Network error');
    }
  }

  private async handleErrorResponse(response: Response): Promise<never> {
    let errorMessage = `HTTP ${response.status}`;
    let validationErrors: any[] | undefined;
    
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
      
      // Handle validation errors (HTTP 422)
      if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
        validationErrors = errorData.detail;
      }
    } catch (e) {
      // If we can't parse the error response, use the status text
      errorMessage = response.statusText || errorMessage;
    }
    
    throw new ApiError(response.status, errorMessage, validationErrors);
  }

  // Authentication endpoints
  async register(data: RegisterData): Promise<User> {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async login(credentials: LoginCredentials): Promise<AuthTokens> {
    return this.request<AuthTokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async refreshToken(refreshToken: string): Promise<AuthTokens | null> {
    try {
      return await this.request<AuthTokens>('/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (error) {
      // If refresh fails, clear tokens
      this.storage.removeItem('auth_tokens');
      this.storage.removeItem('auth_user');
      return null;
    }
  }

  async logout(refreshToken?: string): Promise<void> {
    if (refreshToken) {
      try {
        await this.request<void>('/auth/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch (error) {
        console.warn('Logout API call failed:', error);
      }
    }
  }

  async logoutAll(): Promise<void> {
    return this.request<void>('/auth/logout-all', {
      method: 'POST',
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Password management endpoints
  async forgotPassword(data: PasswordResetRequest): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async resetPassword(data: PasswordResetConfirm): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async changePassword(data: PasswordChange): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Email verification endpoints
  async verifyEmail(data: EmailVerificationConfirm): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async resendVerification(data: EmailVerificationRequest): Promise<{ message: string }> {
    return this.request<{ message: string }>('/auth/resend-verification', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // OAuth endpoints
  async getOAuthProviders(): Promise<{ providers: OAuthProviderInfo[] }> {
    return this.request<{ providers: OAuthProviderInfo[] }>('/auth/providers');
  }

  async initiateOAuth(provider: string, redirectUri?: string): Promise<{ authorization_url: string; state: string }> {
    const params = new URLSearchParams();
    if (redirectUri) {
      params.append('redirect_uri', redirectUri);
    }
    
    return this.request<{ authorization_url: string; state: string }>(`/auth/login/${provider}?${params}`);
  }

  // Organization endpoints
  async getOrganizations(): Promise<OrganizationMembership[]> {
    return this.request<OrganizationMembership[]>('/organizations');
  }

  async getOrganization(id: string): Promise<Organization> {
    return this.request<Organization>(`/organizations/${id}`);
  }

  async createOrganization(data: OrganizationCreateRequest): Promise<Organization> {
    return this.request<Organization>('/organizations', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateOrganization(id: string, data: OrganizationUpdateRequest): Promise<Organization> {
    return this.request<Organization>(`/organizations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteOrganization(id: string): Promise<void> {
    return this.request<void>(`/organizations/${id}`, {
      method: 'DELETE',
    });
  }

  // Invitation endpoints
  async getInvitations(organizationId: string): Promise<Invitation[]> {
    return this.request<Invitation[]>(`/invites?organization_id=${organizationId}`);
  }

  async createInvitation(data: InvitationCreateRequest): Promise<Invitation> {
    return this.request<Invitation>('/invites', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async acceptInvitation(token: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/invites/accept/${token}`, {
      method: 'POST',
    });
  }

  async declineInvitation(token: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/invites/decline/${token}`, {
      method: 'POST',
    });
  }

  // Membership endpoints
  async getOrganizationMembers(organizationId: string): Promise<any[]> {
    return this.request<any[]>(`/memberships?organization_id=${organizationId}`);
  }

  async updateMemberRole(membershipId: string, role: MembershipRole): Promise<any> {
    return this.request<any>(`/memberships/${membershipId}`, {
      method: 'PUT',
      body: JSON.stringify({ role }),
    });
  }

  async removeMember(membershipId: string): Promise<void> {
    return this.request<void>(`/memberships/${membershipId}`, {
      method: 'DELETE',
    });
  }

  // Dashboard endpoints
  async getDashboardStats(): Promise<any> {
    return this.request<any>('/dashboard/stats');
  }

  async getRecentActivities(): Promise<any[]> {
    return this.request<any[]>('/dashboard/recent-activities');
  }

  // Contact endpoints
  async getContacts(): Promise<any[]> {
    return this.request<any[]>('/contacts');
  }

  async getContact(id: string): Promise<any> {
    return this.request<any>(`/contacts/${id}`);
  }

  async createContact(contact: any): Promise<any> {
    return this.request<any>('/contacts', {
      method: 'POST',
      body: JSON.stringify(contact),
    });
  }

  async updateContact(id: string, contact: any): Promise<any> {
    return this.request<any>(`/contacts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(contact),
    });
  }

  async deleteContact(id: string): Promise<void> {
    return this.request<void>(`/contacts/${id}`, {
      method: 'DELETE',
    });
  }

  // Deal endpoints
  async getDeals(): Promise<any[]> {
    return this.request<any[]>('/deals');
  }

  async getDeal(id: string): Promise<any> {
    return this.request<any>(`/deals/${id}`);
  }

  async createDeal(deal: any): Promise<any> {
    return this.request<any>('/deals', {
      method: 'POST',
      body: JSON.stringify(deal),
    });
  }

  async updateDeal(id: string, deal: any): Promise<any> {
    return this.request<any>(`/deals/${id}`, {
      method: 'PUT',
      body: JSON.stringify(deal),
    });
  }

  async deleteDeal(id: string): Promise<void> {
    return this.request<void>(`/deals/${id}`, {
      method: 'DELETE',
    });
  }

  // Activity endpoints
  async getActivities(): Promise<any[]> {
    return this.request<any[]>('/activities');
  }

  async getActivity(id: string): Promise<any> {
    return this.request<any>(`/activities/${id}`);
  }

  async createActivity(activity: any): Promise<any> {
    return this.request<any>('/activities', {
      method: 'POST',
      body: JSON.stringify(activity),
    });
  }

  async updateActivity(id: string, activity: any): Promise<any> {
    return this.request<any>(`/activities/${id}`, {
      method: 'PUT',
      body: JSON.stringify(activity),
    });
  }

  async deleteActivity(id: string): Promise<void> {
    return this.request<void>(`/activities/${id}`, {
      method: 'DELETE',
    });
  }
}

// Export singleton instance
export const api = new ApiClient();
export { ApiClient, ApiError, LocalStorageAdapter };
export type { StorageAdapter }; 