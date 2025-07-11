import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { PasswordResetConfirm } from '../types/auth';
import { 
  validatePassword, 
  validatePasswordStrength, 
  validateConfirmPassword, 
  calculatePasswordStrength,
  getPasswordStrengthColor,
  getPasswordStrengthText
} from '../utils/validation';

const ResetPassword = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { resetPassword, isLoading, error, isAuthenticated, clearError } = useAuth();
  
  const [formData, setFormData] = useState<PasswordResetConfirm>({
    token: '',
    new_password: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [resetSuccess, setResetSuccess] = useState(false);
  const [message, setMessage] = useState('');

  // Get token from URL
  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      setFormData(prev => ({ ...prev, token }));
    } else {
      navigate('/forgot-password', { replace: true });
    }
  }, [searchParams, navigate]);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Password strength calculation using shared utility
  useEffect(() => {
    setPasswordStrength(calculatePasswordStrength(formData.new_password));
  }, [formData.new_password]);

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      new_password: e.target.value,
    }));
    
    // Clear error when user starts typing
    if (error) {
      clearError();
    }
    setMessage('');
  };

  const handleConfirmPasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfirmPassword(e.target.value);
    
    // Clear error when user starts typing
    if (error) {
      clearError();
    }
    setMessage('');
  };

  const validateForm = () => {
    if (!formData.new_password) {
      return 'Password is required.';
    }

    if (!validatePassword(formData.new_password)) {
      return 'Password must be at least 8 characters long.';
    }

    if (!validateConfirmPassword(formData.new_password, confirmPassword)) {
      return 'Passwords do not match.';
    }

    // For stronger validation, you could also use:
    // const strengthCheck = validatePasswordStrength(formData.new_password);
    // if (!strengthCheck.isValid) {
    //   return strengthCheck.errors[0];
    // }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting || isLoading) return;

    const validationError = validateForm();
    if (validationError) {
      setMessage(validationError);
      return;
    }

    try {
      setIsSubmitting(true);
      clearError();
      setMessage('');
      
      const response = await resetPassword(formData);
      setMessage(response);
      setResetSuccess(true);
    } catch (error) {
      // Error is handled by the auth hook
      console.error('Password reset failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (resetSuccess) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-xl shadow-lg p-8 text-center">
            <div className="mx-auto h-16 w-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
              <span className="text-2xl text-green-600">✓</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-4">Password Reset Successful!</h1>
            <p className="text-gray-600 mb-6">
              {message || 'Your password has been successfully reset. You can now log in with your new password.'}
            </p>
            <Link
              to="/login"
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition-colors inline-block text-center"
            >
              Go to Login
            </Link>
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

  const validationError = validateForm();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="mx-auto h-16 w-16 bg-indigo-600 rounded-full flex items-center justify-center mb-4">
            <span className="text-2xl text-white font-bold">TC</span>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">Reset Password</h1>
          <p className="text-gray-600 mt-2">Enter your new password below</p>
        </div>

        {/* Error Message */}
        {(error || message) && !resetSuccess && (
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
            {/* New Password */}
            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-2">
                New Password
              </label>
              <div className="relative">
                <input
                  id="new_password"
                  name="new_password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={formData.new_password}
                  onChange={handlePasswordChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent pr-10"
                  placeholder="Enter your new password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  <span className="text-gray-400 hover:text-gray-600">
                    {showPassword ? '🙈' : '👁️'}
                  </span>
                </button>
              </div>
              
              {/* Password Strength Indicator */}
              {formData.new_password && (
                <div className="mt-2">
                  <div className="flex items-center space-x-2">
                    <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-300 ${getPasswordStrengthColor(passwordStrength)}`}
                        style={{ width: `${(passwordStrength / 5) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-600 min-w-0">
                      {getPasswordStrengthText(passwordStrength)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Use 8+ characters with uppercase, lowercase, numbers, and symbols
                  </p>
                </div>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                Confirm New Password
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  value={confirmPassword}
                  onChange={handleConfirmPasswordChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent pr-10"
                  placeholder="Confirm your new password"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  <span className="text-gray-400 hover:text-gray-600">
                    {showConfirmPassword ? '🙈' : '👁️'}
                  </span>
                </button>
              </div>
              {confirmPassword && formData.new_password !== confirmPassword && (
                <p className="text-xs text-red-600 mt-1">Passwords do not match</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting || isLoading || !!validationError}
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Resetting Password...
                </span>
              ) : (
                'Reset Password'
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

export default ResetPassword; 
 
 
 
