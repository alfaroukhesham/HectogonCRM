import React from 'react';
import { NavLink } from 'react-router-dom';
import { useNavigation } from '../hooks/useNavigation';

const Navigation: React.FC = () => {
  const { navigationItems, isCurrentPath } = useNavigation();

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold text-gray-900">TinyCRM</h1>
            </div>
            <div className="ml-6 flex space-x-8">
              {navigationItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                      isActive || isCurrentPath(item.to)
                        ? 'border-blue-500 text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`
                  }
                  title={item.description}
                >
                  <span className="mr-2">{item.icon}</span>
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
          
          {/* Optional: User menu or actions */}
          <div className="flex items-center">
            <div className="text-sm text-gray-500">
              Welcome to TinyCRM
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 