import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { LoginCredentials, OAuthProviderInfo } from '../types/auth';
import { api } from '../utils/api';

const Login = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { login, initiateOAuth, handleOAuthCallback, isLoading, error, isAuthenticated, clearError } = useAuth();
  
  // Form state
  const [credentials, setCredentials] = useState<LoginCredentials>({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [oauthProviders, setOauthProviders] = useState<OAuthProviderInfo[]>([]);
  const [authMethod, setAuthMethod] = useState<'password' | 'oauth'>('password');

  // Handle OAuth callback
  useEffect(() => {
    const handleCallback = async () => {
      const accessToken = searchParams.get('access_token');
      const refreshToken = searchParams.get('refresh_token');
      const oauthError = searchParams.get('error');

      // Validate token format before processing
      if (accessToken && (!accessToken.match(/^[A-Za-z0-9_-]+$/) || accessToken.length < 10)) {
        console.error('Invalid access token format');
        navigate('/login?error=oauth_callback_failed', { replace: true });
        return;
      }
      
      if (refreshToken && (!refreshToken.match(/^[A-Za-z0-9_-]+$/) || refreshToken.length < 10)) {
        console.error('Invalid refresh token format');
        navigate('/login?error=oauth_callback_failed', { replace: true });
        return;
      }

      if (oauthError) {
        // Sanitize error parameter to prevent XSS
        const sanitizedError = oauthError.replace(/[^a-zA-Z0-9_-]/g, '');
        console.error('OAuth error:', sanitizedError);
        navigate('/login?error=oauth_failed', { replace: true });
        return;
      }

      if (accessToken && refreshToken) {
        try {
          await handleOAuthCallback(accessToken, refreshToken);
          navigate('/dashboard', { replace: true });
        } catch (error) {
          console.error('OAuth callback failed:', error);
          navigate('/login?error=oauth_callback_failed', { replace: true });
        }
      }
    };

    if (window.location.pathname === '/oauth/callback') {
      handleCallback();
    }
  }, [searchParams, handleOAuthCallback, navigate]);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Load OAuth providers
  useEffect(() => {
    const loadProviders = async () => {
      try {
        const response = await api.getOAuthProviders();
        setOauthProviders(response.providers);
      } catch (error) {
        console.error('Failed to load OAuth providers:', error);
      }
    };

    loadProviders();
  }, []);

  // Handle URL error parameter
  useEffect(() => {
    const urlError = searchParams.get('error');
    if (urlError) {
      let errorMessage = 'Authentication failed. Please try again.';
      
      switch (urlError) {
        case 'oauth_failed':
          errorMessage = 'OAuth authentication failed. Please try again.';
          break;
        case 'oauth_callback_failed':
          errorMessage = 'OAuth callback failed. Please try again.';
          break;
        case 'token_expired':
          errorMessage = 'Your session has expired. Please log in again.';
          break;
      }
      
      // Set error without overriding existing errors
      if (!error) {
        // We can't call setError directly, so we'll handle this in the UI
        console.error(errorMessage);
      }
    }
  }, [searchParams, error]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value,
    }));
    
    // Clear error when user starts typing
    if (error) {
      clearError();
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting || isLoading) return;

    try {
      setIsSubmitting(true);
      clearError();
      
      await login(credentials);
      navigate('/dashboard', { replace: true });
    } catch (error) {
      // Error is handled by the auth hook
      console.error('Login failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOAuthLogin = async (provider: string) => {
    if (isLoading) return;

    try {
      clearError();
      await initiateOAuth(provider);
    } catch (error) {
      console.error('OAuth initiation failed:', error);
    }
  };

  const getProviderIcon = (provider: string) => {
    switch (provider) {
      case 'google':
        return '🔍';
      case 'facebook':
        return '👥';
      case 'twitter':
        return '🐦';
      default:
        return '🔐';
    }
  };

  if (isLoading && !isSubmitting) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl text-white font-bold">TC</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Welcome back</h1>
          <p className="text-gray-600 mt-2">Sign in to your Tiny CRM account</p>
        </div>

        {/* Error Message */}
        {error && (
          <div id="auth-error" className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg" role="alert" aria-live="polite">
            <div className="flex items-center">
              <span className="text-red-600 mr-2">⚠️</span>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* URL Error Message */}
        {searchParams.get('error') && !error && (
          <div id="url-error" className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg" role="alert" aria-live="polite">
            <div className="flex items-center">
              <span className="text-red-600 mr-2">⚠️</span>
              <p className="text-red-700 text-sm">
                {searchParams.get('error') === 'oauth_failed' && 'OAuth authentication failed. Please try again.'}
                {searchParams.get('error') === 'oauth_callback_failed' && 'OAuth callback failed. Please try again.'}
                {searchParams.get('error') === 'token_expired' && 'Your session has expired. Please log in again.'}
                {!['oauth_failed', 'oauth_callback_failed', 'token_expired'].includes(searchParams.get('error') || '') && 'Authentication failed. Please try again.'}
              </p>
            </div>
          </div>
        )}

        {/* Main Card */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          {/* Auth Method Toggle */}
          <div className="flex mb-6 bg-gray-100 rounded-lg p-1" role="tablist" aria-label="Authentication method selection">
            <button
              type="button"
              role="tab"
              aria-selected={authMethod === 'password'}
              aria-controls="password-panel"
              onClick={() => setAuthMethod('password')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                authMethod === 'password'
                  ? 'bg-white text-indigo-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Email & Password
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={authMethod === 'oauth'}
              aria-controls="oauth-panel"
              onClick={() => setAuthMethod('oauth')}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                authMethod === 'oauth'
                  ? 'bg-white text-indigo-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Social Login
            </button>
          </div>

          {/* Password Authentication */}
          {authMethod === 'password' && (
            <div id="password-panel" role="tabpanel" aria-labelledby="password-tab">
              <form onSubmit={handlePasswordLogin} className="space-y-6">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email address
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    aria-label="Email address"
                    aria-describedby={error ? "auth-error" : undefined}
                    value={credentials.email}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    placeholder="Enter your email"
                  />
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="current-password"
                      required
                      aria-label="Password"
                      aria-describedby={error ? "auth-error" : "password-toggle"}
                      value={credentials.password}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent pr-10"
                      placeholder="Enter your password"
                    />
                    <button
                      type="button"
                      id="password-toggle"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                    >
                      <span className="text-gray-400 hover:text-gray-600">
                        {showPassword ? '🙈' : '👁️'}
                      </span>
                    </button>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <Link
                    to="/forgot-password"
                    className="text-sm text-indigo-600 hover:text-indigo-500"
                  >
                    Forgot your password?
                  </Link>
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || isLoading}
                  aria-describedby={isSubmitting ? "submit-status" : undefined}
                  className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {isSubmitting ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      <span id="submit-status">Signing in...</span>
                    </span>
                  ) : (
                    'Sign in'
                  )}
                </button>
              </form>
            </div>
          )}

          {/* OAuth Authentication */}
          {authMethod === 'oauth' && (
            <div id="oauth-panel" role="tabpanel" aria-labelledby="oauth-tab" className="space-y-4">
              {oauthProviders.length > 0 ? (
                <>
                  <p className="text-sm text-gray-600 text-center mb-4">
                    Choose your preferred social login method
                  </p>
                  {oauthProviders.map((provider) => (
                    <button
                      key={provider.name}
                      onClick={() => handleOAuthLogin(provider.name)}
                      disabled={isLoading}
                      aria-label={`Continue with ${provider.display_name}`}
                      className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <span className="text-xl mr-3" aria-hidden="true">{getProviderIcon(provider.name)}</span>
                      <span className="text-gray-700 font-medium">
                        Continue with {provider.display_name}
                      </span>
                    </button>
                  ))}
                </>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500">No OAuth providers configured</p>
                  <button
                    onClick={() => setAuthMethod('password')}
                    className="mt-2 text-indigo-600 hover:text-indigo-500 text-sm"
                  >
                    Use email and password instead
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Sign up link */}
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-600">
              Don't have an account?{' '}
              <Link
                to="/register"
                className="text-indigo-600 hover:text-indigo-500 font-medium"
              >
                Sign up
              </Link>
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500">
            By signing in, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login; 
 
 
 
