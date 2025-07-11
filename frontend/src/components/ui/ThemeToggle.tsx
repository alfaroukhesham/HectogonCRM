import React from 'react';
import { useTheme } from '../../hooks/useTheme';

const ThemeToggle: React.FC = () => {
  const { theme, setTheme } = useTheme();

  const handleToggle = () => {
    setTheme(theme === 'light' ? 'dark' : 'light');
  };

  const getTogglePosition = () => {
    return theme === 'light' ? 'translate-x-0' : 'translate-x-6';
  };

  const getBackgroundColor = () => {
    return theme === 'light' 
      ? 'bg-gradient-to-r from-yellow-400 to-orange-500' 
      : 'bg-gradient-to-r from-indigo-600 to-purple-700';
  };

  const getCurrentIcon = () => {
    return theme === 'light' ? '☀️' : '🌙';
  };

  return (
    <div className="relative">
      <button
        onClick={handleToggle}
        className={`
          relative w-14 h-8 rounded-full transition-all duration-500 ease-out
          ${getBackgroundColor()}
          shadow-lg hover:shadow-xl
          transform hover:scale-105 active:scale-95
          focus:outline-none focus:ring-4 focus:ring-blue-500/30
          group
        `}
        title={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
      >
        {/* Background Track Icons */}
        <div className="absolute inset-0 flex items-center justify-around px-1 text-white/60 text-xs">
          <span className="transform scale-75">☀️</span>
          <span className="transform scale-75">🌙</span>
        </div>
        
        {/* Sliding Toggle */}
        <div
          className={`
            absolute top-0.5 left-0.5 w-7 h-7 
            bg-white dark:bg-gray-100
            rounded-full shadow-lg
            transform transition-all duration-500 ease-out
            ${getTogglePosition()}
            flex items-center justify-center
            group-hover:shadow-xl
            border-2 border-white/20
          `}
        >
          <span className="text-sm animate-pulse">
            {getCurrentIcon()}
          </span>
        </div>
        
        {/* Glow Effect */}
        <div className={`
          absolute inset-0 rounded-full opacity-0 group-hover:opacity-30 
          transition-opacity duration-300
          ${getBackgroundColor()}
          blur-md scale-110
        `} />
      </button>
    </div>
  );
};

export default ThemeToggle;
