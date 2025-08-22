import React from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopNavbar from './TopNavbar';
import { useOrganization } from '../hooks/useOrganization';

interface MainLayoutProps {
  children?: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const { isLoading, currentOrganization, error, retryLoading } = useOrganization();

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  // While the organization data is loading, show a loading indicator
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-xl text-gray-700 dark:text-gray-300">Loading Organization...</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Setting up your workspace</p>
        </div>
      </div>
    );
  }

  // If there's an error loading organizations, show error state with retry option
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-red-500 mb-4">
            <svg className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Organization Loading Failed</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-6">{error}</p>
          <button
            onClick={retryLoading}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // If loading is finished but there's no organization, prompt the user
  if (!currentOrganization) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center max-w-md mx-auto p-6">
          <div className="text-gray-400 mb-4">
            <svg className="h-16 w-16 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-4m-5 0H9m0 0H5m0 0h2M7 7h10M7 11h10M7 15h10" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">No Organization Found</h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Please create or join an organization to continue using TinyCRM.
          </p>
          <button
            onClick={() => window.location.href = '/organizations'}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition-colors"
          >
            Manage Organizations
          </button>
        </div>
      </div>
    );
  }

  // Once loading is complete AND an organization is set, render the app
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300 flex">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onToggle={toggleSidebar} />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col lg:ml-0">
        {/* Top Navigation */}
        <TopNavbar onSidebarToggle={toggleSidebar} />
        
        {/* Main Content */}
        <main className="flex-1 overflow-auto">
          <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
            <div className="px-4 py-6 sm:px-0">
              {children || <Outlet />}
            </div>
          </div>
        </main>
        
        {/* Footer */}
        <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 transition-colors duration-300">
          <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                © 2024 TinyCRM. Built with React & TypeScript.
              </p>
              <div className="flex space-x-4">
                <a href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors">
                  Help
                </a>
                <a href="#" className="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors">
                  Support
                </a>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default MainLayout;
