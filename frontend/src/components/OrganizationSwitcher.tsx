import React, { useState } from 'react';
import { useOrganization } from '../hooks/useOrganization';
import { useAuth } from '../hooks/useAuth';

interface OrganizationSwitcherProps {
  className?: string;
}

export const OrganizationSwitcher: React.FC<OrganizationSwitcherProps> = ({ className = '' }) => {
  const { currentOrganization, organizations, switchOrganization, isLoading } = useOrganization();
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);

  if (!user || isLoading || organizations.length === 0) {
    return (
      <div className={`animate-pulse ${className}`}>
        <div className="h-10 bg-gray-200 rounded-lg"></div>
      </div>
    );
  }

  if (organizations.length === 1) {
    return (
      <div className={`flex items-center space-x-3 px-3 py-2 rounded-lg bg-gray-50 ${className}`}>
        {currentOrganization?.logo_url ? (
          <img 
            src={currentOrganization.logo_url} 
            alt={currentOrganization.name}
            className="w-8 h-8 rounded-full object-cover"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold text-sm">
            {currentOrganization?.name.charAt(0).toUpperCase() || 'O'}
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-gray-900 truncate">
            {currentOrganization?.name || 'Loading...'}
          </p>
          <p className="text-xs text-gray-500">
            {organizations[0]?.role === 'admin' && '👑 Admin'}
            {organizations[0]?.role === 'editor' && '✏️ Editor'}
            {organizations[0]?.role === 'viewer' && '👁️ Viewer'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative w-full ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center space-x-3 px-3 py-2 rounded-xl bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors shadow-sm"
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        {currentOrganization?.logo_url ? (
          <img 
            src={currentOrganization.logo_url} 
            alt={currentOrganization.name}
            className="w-8 h-8 rounded-full object-cover flex-shrink-0"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
            {currentOrganization?.name.charAt(0).toUpperCase() || 'O'}
          </div>
        )}
        <div className="flex-1 min-w-0 text-left">
          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
            {currentOrganization?.name || 'Select Organization'}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {organizations.find(org => org.organization_id === currentOrganization?.id)?.role === 'admin' && '👑 Admin'}
            {organizations.find(org => org.organization_id === currentOrganization?.id)?.role === 'editor' && '✏️ Editor'}
            {organizations.find(org => org.organization_id === currentOrganization?.id)?.role === 'viewer' && '👁️ Viewer'}
          </p>
        </div>
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          
          {/* Dropdown */}
          <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-600 z-20 max-h-64 overflow-y-auto">
            <div className="py-1">
              {organizations.map((org) => (
                <button
                  key={org.organization_id}
                  onClick={async () => {
                    try {
                      await switchOrganization(org.organization_id);
                      setIsOpen(false);
                    } catch (error) {
                      console.error('Failed to switch organization:', error);
                      // TODO: Show user-friendly error message
                    }
                  }}
                  className={`w-full flex items-center space-x-3 px-3 py-2 text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50 transition-colors ${
                    currentOrganization?.id === org.organization_id ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400' : 'text-gray-900 dark:text-white hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                  role="option"
                  aria-selected={currentOrganization?.id === org.organization_id}
                >
                  {org.organization_logo_url ? (
                    <img 
                      src={org.organization_logo_url} 
                      alt={org.organization_name}
                      className="w-8 h-8 rounded-full object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
                      {org.organization_name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate text-gray-900 dark:text-white">
                      {org.organization_name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {org.role === 'admin' && '👑 Admin'}
                      {org.role === 'editor' && '✏️ Editor'}
                      {org.role === 'viewer' && '👁️ Viewer'}
                    </p>
                  </div>
                  {currentOrganization?.id === org.organization_id && (
                    <svg className="w-5 h-5 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  )}
                </button>
              ))}
            </div>
            
            <div className="border-t border-gray-200 py-1">
              <div className="border-t border-gray-200 dark:border-gray-600 py-1">
                <button
                  onClick={() => {
                    setIsOpen(false);
                    // TODO: Open create organization modal
                  }}
                  className="w-full flex items-center space-x-3 px-3 py-2 text-left text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-700 transition-colors"
                >
                  <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-600 flex items-center justify-center flex-shrink-0">
                    <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                  </div>
                  <span className="text-sm font-medium">Create Organization</span>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}; 
