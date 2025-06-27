import React from 'react';
import { NavLink } from 'react-router-dom';
import { useNavigation } from '../hooks/useNavigation';
import ThemeToggle from './ui/ThemeToggle';

const Navigation: React.FC = () => {
  const { navigationItems, isCurrentPath } = useNavigation();

  return (
    <nav className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-md shadow-sm border-b border-gray-200/60 dark:border-gray-700/60 transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
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
            <div className="ml-6 flex space-x-8">
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
            </div>
          </div>
          
          {/* Right side with theme toggle */}
          <div className="flex items-center space-x-4">
            <ThemeToggle />
            <div className="hidden md:flex items-center text-sm text-gray-500 dark:text-gray-400">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-2"></div>
              Online
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;