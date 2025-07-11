import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useOrganization } from '../hooks/useOrganization';
import { MembershipRole } from '../types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: 'admin' | 'editor' | 'viewer';
  requiredOrganizationRole?: MembershipRole;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ 
  children, 
  requiredRole = 'viewer',
  requiredOrganizationRole 
}) => {
  const { user, isLoading, isAuthenticated } = useAuth();
  const { userRole: organizationRole, isLoading: orgLoading, currentOrganization } = useOrganization();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (isLoading || orgLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p className="text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated || !user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check organization role permissions if required
  if (requiredOrganizationRole) {
    if (!currentOrganization || !organizationRole) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg p-8 text-center">
            <div className="mb-4">
              <svg className="mx-auto h-12 w-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Access Denied
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              You don't have permission to access this page in this organization.
            </p>
            <button
              onClick={() => window.history.back()}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors duration-200"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }

    // Check organization role hierarchy
    const orgRoleHierarchy = {
      [MembershipRole.VIEWER]: 1,
      [MembershipRole.EDITOR]: 2,
      [MembershipRole.ADMIN]: 3,
    };

    const userOrgLevel = orgRoleHierarchy[organizationRole] || 0;
    const requiredOrgLevel = orgRoleHierarchy[requiredOrganizationRole] || 0;

    if (userOrgLevel < requiredOrgLevel) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="max-w-md w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg p-8 text-center">
            <div className="mb-4">
              <svg className="mx-auto h-12 w-12 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              Insufficient Permissions
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Required role: {requiredOrganizationRole}, Your role: {organizationRole}
            </p>
            <button
              onClick={() => window.history.back()}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors duration-200"
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }

    return <>{children}</>;
  }

  // Note: User-level role checks are handled by organization-based permissions
  // The backend uses organization-based roles via requiredOrganizationRole parameter

  return <>{children}</>;
};

export default ProtectedRoute; 
