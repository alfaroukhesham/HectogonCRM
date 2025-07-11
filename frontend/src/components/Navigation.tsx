import React from 'react';
import { NavLink } from 'react-router-dom';
import { useNavigation } from '../hooks/useNavigation';
import { useAuth } from '../hooks/useAuth';
import { useOrganization } from '../hooks/useOrganization';
import { OrganizationSwitcher } from './OrganizationSwitcher';
import ThemeToggle from './ui/ThemeToggle';
import { navigationRoutes, organizationRoutes } from '../router/routes';
import { useState, useRef, useEffect } from 'react';

const Navigation: React.FC = () => {
  const { navigationItems, isCurrentPath } = useNavigation();
  const { user, logout } = useAuth();
  const { currentOrganization, userRole } = useOrganization();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    setShowUserMenu(false);
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
      case 'editor':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'viewer':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  // Filter organization routes based on user role
  const availableOrgRoutes = organizationRoutes.filter(route => {
    if (!route.requiresRole) return true;
    if (!userRole) return false;
    
    const roleHierarchy = { viewer: 1, editor: 2, admin: 3 };
    const userLevel = roleHierarchy[userRole] || 0;
    const requiredLevel = roleHierarchy[route.requiresRole] || 0;
    
    return userLevel >= requiredLevel;
  });

  return (
    <nav className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-md shadow-sm border-b border-gray-200/60 dark:border-gray-700/60 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center space-x-6">
            <div className="flex-shrink-0 flex items-center">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">TC</span>
                </div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                  TinyCRM
                </h1>
              </div>
            </div>

            {/* Organization Switcher */}
            {user && (
              <div className="w-64">
                <OrganizationSwitcher />
              </div>
            )}
          </div>

          {/* Navigation Links */}
          <div className="flex items-center">
            <div className="flex space-x-8">
              {/* Main navigation */}
              {navigationItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-all duration-200 ${
                      isActive || isCurrentPath(item.to)
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-300'
                    }`
                  }
                  title={item.description}
                >
                  <span className="mr-2 text-base">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}

              {/* Organization management routes */}
              {availableOrgRoutes.map((route) => (
                <NavLink
                  key={route.path}
                  to={route.path}
                  className={({ isActive }) =>
                    `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-all duration-200 ${
                      isActive || isCurrentPath(route.path)
                        ? 'border-purple-500 text-purple-600 dark:text-purple-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 dark:hover:border-gray-600 hover:text-gray-700 dark:hover:text-gray-300'
                    }`
                  }
                  title={route.description}
                >
                  <span className="mr-2 text-base">{route.icon}</span>
                  {route.label}
                </NavLink>
              ))}
            </div>
          </div>
          
          {/* Right side with theme toggle and user menu */}
          <div className="flex items-center space-x-6">
            <ThemeToggle />
            
            {user ? (
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  className="flex items-center space-x-3 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 p-2 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200"
                >
                  {user.avatar_url ? (
                    <img
                      className="h-8 w-8 rounded-full"
                      src={user.avatar_url}
                      alt={user.full_name}
                    />
                  ) : (
                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                      <span className="text-white font-medium text-sm">
                        {user.full_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  )}
                  <div className="hidden lg:flex flex-col items-start">
                    <span className="text-gray-700 dark:text-gray-200 font-medium">
                      {user.full_name}
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getRoleColor(user.role)}`}>
                        {user.role}
                      </span>
                      {userRole && userRole !== user.role && (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getRoleColor(userRole)}`}>
                          {userRole} in org
                        </span>
                      )}
                    </div>
                  </div>
                  <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {showUserMenu && (
                  <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 rounded-md shadow-lg py-1 z-50 border border-gray-200 dark:border-gray-700">
                    <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                      <div className="flex items-center space-x-3">
                        {user.avatar_url ? (
                          <img
                            className="h-10 w-10 rounded-full"
                            src={user.avatar_url}
                            alt={user.full_name}
                          />
                        ) : (
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                            <span className="text-white font-medium">
                              {user.full_name.charAt(0).toUpperCase()}
                            </span>
                          </div>
                        )}
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {user.full_name}
                          </p>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {user.email}
                          </p>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className={`inline-block text-xs px-2 py-0.5 rounded-full ${getRoleColor(user.role)}`}>
                              Global: {user.role}
                            </span>
                            {userRole && userRole !== user.role && (
                              <span className={`inline-block text-xs px-2 py-0.5 rounded-full ${getRoleColor(userRole)}`}>
                                Org: {userRole}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      {currentOrganization && (
                        <div className="mt-2 pt-2 border-t border-gray-100 dark:border-gray-600">
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Current Organization:
                          </p>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {currentOrganization.name}
                          </p>
                        </div>
                      )}
                    </div>
                    
                    <div className="py-1">
                      <div className="px-4 py-2 text-xs text-gray-500 dark:text-gray-400">
                        Connected via: {user.auth_methods.join(', ')}
                      </div>
                      
                      <button
                        onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center space-x-2"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        <span>Sign out</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="hidden md:flex items-center text-sm text-gray-500 dark:text-gray-400">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse mr-2"></div>
                Not authenticated
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
