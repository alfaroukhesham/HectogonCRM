import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { PasswordResetRequest } from '../types/auth';
import { validateEmail } from '../utils/validation';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const { forgotPassword, isLoading, error, isAuthenticated, clearError } = useAuth();
  
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [message, setMessage] = useState('');

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    
    // Clear error when user starts typing
    if (error) {
      clearError();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting || isLoading) return;

    if (!email) {
      setMessage('Please enter your email address.');
      return;
    }

    if (!validateEmail(email)) {
      setMessage('Please enter a valid email address.');
      return;
    }

    try {
      setIsSubmitting(true);
      clearError();
      setMessage('');
      
      const response = await forgotPassword({ email });
      setMessage(response);
      setEmailSent(true);
    } catch (error) {
      // Error is handled by the auth hook
      console.error('Password reset request failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (emailSent) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="mx-auto h-16 w-16 bg-blue-100 rounded-full flex items-center justify-center mb-6">
              <span className="text-2xl text-blue-600">📧</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Check Your Email</h1>
            <p className="text-gray-600 mb-6">
              {message || `We've sent password reset instructions to ${email}.`}
            </p>
            <div className="space-y-4">
              <Link
                to="/login"
                className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors inline-block text-center"
              >
                Back to Login
              </Link>
              <button
                onClick={() => {
                  setEmailSent(false);
                  setEmail('');
                  setMessage('');
                }}
                className="w-full text-indigo-600 hover:text-indigo-500 text-sm"
              >
                Try a different email address
              </button>
            </div>
            <div className="mt-6 pt-6 border-t border-gray-200">
              <p className="text-sm text-gray-500">
                Didn't receive the email? Check your spam folder or wait a few minutes and try again.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

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
          <h1 className="text-3xl font-bold text-gray-900">Forgot Password?</h1>
          <p className="text-gray-600 mt-2">No worries, we'll send you reset instructions</p>
        </div>

        {/* Error Message */}
        {(error || message) && !emailSent && (
          <div className={`mb-6 p-4 border rounded-lg ${
            error ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'
          }`}>
            <div className="flex items-center">
              <span className={`mr-2 ${error ? 'text-red-600' : 'text-blue-600'}`}>
                {error ? '⚠️' : 'ℹ️'}
              </span>
              <p className={`text-sm ${error ? 'text-red-700' : 'text-blue-700'}`}>
                {error || message}
              </p>
            </div>
          </div>
        )}

        {/* Main Card */}
        <div className="bg-white rounded-xl shadow-lg p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                placeholder="Enter your email address"
              />
              <p className="text-sm text-gray-500 mt-2">
                Enter the email address associated with your account and we'll send you a link to reset your password.
              </p>
            </div>

            <button
              type="submit"
              disabled={isSubmitting || isLoading || !email || !validateEmail(email)}
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Sending Reset Link...
                </span>
              ) : (
                'Send Reset Link'
              )}
            </button>
          </form>

          {/* Back to login link */}
          <div className="mt-8 text-center">
            <Link
              to="/login"
              className="text-sm text-indigo-600 hover:text-indigo-500 font-medium"
            >
              ← Back to Login
            </Link>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-xs text-gray-500">
            Remember your password?{' '}
            <Link to="/login" className="text-indigo-600 hover:text-indigo-500">
              Sign in instead
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword; 
 
 
 
