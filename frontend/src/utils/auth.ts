import type { User, AuthTokens } from '../types/auth';

const TOKEN_KEY = 'tiny_crm_tokens';
const USER_KEY = 'tiny_crm_user';

export class AuthStorage {
  static setTokens(tokens: AuthTokens): void {
    try {
      localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
    } catch (error) {
      console.error('Failed to store tokens:', error);
    }
  }

  static getTokens(): AuthTokens | null {
    try {
      const tokens = localStorage.getItem(TOKEN_KEY);
      return tokens ? JSON.parse(tokens) : null;
    } catch (error) {
      console.error('Failed to retrieve tokens:', error);
      return null;
    }
  }

  static setUser(user: User): void {
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(user));
    } catch (error) {
      console.error('Failed to store user:', error);
    }
  }

  static getUser(): User | null {
    try {
      const user = localStorage.getItem(USER_KEY);
      return user ? JSON.parse(user) : null;
    } catch (error) {
      console.error('Failed to retrieve user:', error);
      return null;
    }
  }

  static clear(): void {
    try {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    } catch (error) {
      console.error('Failed to clear storage:', error);
    }
  }

  static isTokenExpired(token: string): boolean {
    try {
      const parts = token.split('.');
      if (parts.length !== 3 || !parts[1]) return true;
      
      const payload = JSON.parse(atob(parts[1]));
      const currentTime = Date.now() / 1000;
      return payload.exp < currentTime;
    } catch (error) {
      return true;
    }
  }
}

export class AuthService {
  private static baseUrl = (import.meta as any).env?.VITE_BACKEND_URL || 'http://localhost:8000';

  static async getOAuthProviders() {
    const response = await fetch(`${this.baseUrl}/api/auth/providers`);
    if (!response.ok) {
      throw new Error('Failed to fetch OAuth providers');
    }
    return response.json();
  }

  static async initiateOAuth(provider: string): Promise<{ authorization_url: string; state: string }> {
    const response = await fetch(`${this.baseUrl}/api/auth/login/${provider}?redirect_uri=${encodeURIComponent(window.location.origin)}`);
    if (!response.ok) {
      throw new Error('Failed to initiate OAuth login');
    }
    return response.json();
  }

  static async refreshToken(refreshToken: string): Promise<AuthTokens> {
    const response = await fetch(`${this.baseUrl}/api/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    return response.json();
  }

  static async getCurrentUser(accessToken: string): Promise<User> {
    const response = await fetch(`${this.baseUrl}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get current user');
    }

    return response.json();
  }

  static async logout(refreshToken: string, accessToken: string): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch (error) {
      console.error('Logout request failed:', error);
    } finally {
      AuthStorage.clear();
    }
  }

  static async logoutAll(accessToken: string): Promise<void> {
    try {
      await fetch(`${this.baseUrl}/api/auth/logout-all`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
        },
      });
    } catch (error) {
      console.error('Logout all request failed:', error);
    } finally {
      AuthStorage.clear();
    }
  }
} 