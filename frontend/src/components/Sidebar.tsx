import React, { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useNavigation } from '../hooks/useNavigation';
import { useOrganization } from '../hooks/useOrganization';
import { navigationRoutes, organizationRoutes } from '../router/routes';
import { MembershipRole } from '../types';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onToggle }) => {
  const { isCurrentPath } = useNavigation();
  const { userRole } = useOrganization();
  const location = useLocation();

  // Filter organization routes based on user role
  const availableOrgRoutes = organizationRoutes.filter(route => {
    if (!route.requiresRole) return true;
    if (!userRole) return false;
    
    const roleHierarchy = { viewer: 1, editor: 2, admin: 3 };
    const userLevel = roleHierarchy[userRole] || 0;
    const requiredLevel = roleHierarchy[route.requiresRole] || 0;
    
    return userLevel >= requiredLevel;
  });

  const SidebarLink: React.FC<{
    to: string;
    icon: string;
    label: string;
    description?: string;
    isActive?: boolean;
    onClick?: () => void;
  }> = ({ to, icon, label, description, isActive, onClick }) => (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive: navIsActive }) => {
        const active = isActive || navIsActive || isCurrentPath(to);
        return `
          group flex items-center px-3 py-2.5 text-sm font-medium rounded-xl transition-all duration-200
          ${active 
            ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/25' 
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
          }
        `;
      }}
      title={description}
    >
      <span className="text-lg mr-3 transition-transform duration-200 group-hover:scale-110">
        {icon}
      </span>
      <div className="flex-1 min-w-0">
        <span className="block truncate">{label}</span>
        {description && (
          <span className="text-xs opacity-75 block truncate mt-0.5">
            {description}
          </span>
        )}
      </div>
    </NavLink>
  );

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed top-0 left-0 z-50 h-full bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700
        transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:z-auto
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        w-72 flex flex-col shadow-xl lg:shadow-none
      `}>
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">TC</span>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                TinyCRM
              </h1>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Customer Management
              </p>
            </div>
          </div>
          
          {/* Mobile Close Button */}
          <button
            onClick={onToggle}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation Content */}
        <div className="flex-1 overflow-y-auto py-6 px-4 space-y-8">
          {/* Main Navigation */}
          <div>
            <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 px-3">
              Main Menu
            </h2>
            <nav className="space-y-1">
              {navigationRoutes.map((route) => (
                <SidebarLink
                  key={route.path}
                  to={route.path}
                  icon={route.icon}
                  label={route.label}
                  description={route.description}
                  onClick={() => window.innerWidth < 1024 && onToggle()}
                />
              ))}
            </nav>
          </div>

          {/* Organization Management */}
          {availableOrgRoutes.length > 0 && (
            <div>
              <h2 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3 px-3">
                Organization
              </h2>
              <nav className="space-y-1">
                {availableOrgRoutes.map((route) => (
                  <SidebarLink
                    key={route.path}
                    to={route.path}
                    icon={route.icon}
                    label={route.label}
                    description={route.description}
                    onClick={() => window.innerWidth < 1024 && onToggle()}
                  />
                ))}
              </nav>
            </div>
          )}

          {/* Quick Stats */}
          <div className="bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-4 border border-blue-100 dark:border-blue-800/30">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
              Quick Stats
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Active Deals</span>
                <span className="font-medium text-blue-600 dark:text-blue-400">12</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">New Contacts</span>
                <span className="font-medium text-green-600 dark:text-green-400">8</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Tasks Due</span>
                <span className="font-medium text-orange-600 dark:text-orange-400">3</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-4 text-white">
            <h3 className="font-semibold text-sm mb-1">Upgrade to Pro</h3>
            <p className="text-xs opacity-90 mb-3">
              Unlock advanced features and unlimited contacts
            </p>
            <button className="w-full bg-white/20 hover:bg-white/30 text-white text-xs font-medium py-2 px-3 rounded-lg transition-colors">
              Learn More
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;