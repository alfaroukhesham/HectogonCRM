import React from 'react';
import { useTheme } from '@/hooks/useTheme';

const ThemeToggle: React.FC = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();

  const handleToggle = () => {
    if (theme === 'light') {
      setTheme('dark');
    } else if (theme === 'dark') {
      setTheme('system');
    } else {
      setTheme('light');
    }
  };

  const getTogglePosition = () => {
    switch (theme) {
      case 'light':
        return 'translate-x-0';
      case 'dark':
        return 'translate-x-8';
      case 'system':
        return 'translate-x-16';
      default:
        return 'translate-x-0';
    }
  };

  const getBackgroundColor = () => {
    switch (theme) {
      case 'light':
        return 'bg-gradient-to-r from-yellow-400 to-orange-500';
      case 'dark':
        return 'bg-gradient-to-r from-indigo-600 to-purple-700';
      case 'system':
        return 'bg-gradient-to-r from-blue-500 to-cyan-500';
      default:
        return 'bg-gradient-to-r from-yellow-400 to-orange-500';
    }
  };

  const getCurrentIcon = () => {
    switch (theme) {
      case 'light':
        return '☀️';
      case 'dark':
        return '🌙';
      case 'system':
        return '💻';
      default:
        return '☀️';
    }
  };

  const getThemeLabel = () => {
    switch (theme) {
      case 'light':
        return 'Light';
      case 'dark':
        return 'Dark';
      case 'system':
        return `Auto (${resolvedTheme})`;
      default:
        return 'Light';
    }
  };

  return (
    <div className="flex flex-col items-center space-y-2">
      {/* Toggle Switch */}
      <div className="relative">
        <button
          onClick={handleToggle}
          className={`
            relative w-24 h-8 rounded-full transition-all duration-500 ease-out
            ${getBackgroundColor()}
            shadow-lg hover:shadow-xl
            transform hover:scale-105 active:scale-95
            focus:outline-none focus:ring-4 focus:ring-blue-500/30
            group
          `}
          title={`Switch theme (currently ${getThemeLabel()})`}
        >
          {/* Background Track Icons */}
          <div className="absolute inset-0 flex items-center justify-around px-1 text-white/60 text-xs">
            <span className="transform scale-75">☀️</span>
            <span className="transform scale-75">🌙</span>
            <span className="transform scale-75">💻</span>
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
        
        {/* Active Theme Indicator */}
        <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-white shadow-md flex items-center justify-center">
          <div className={`
            w-1.5 h-1.5 rounded-full animate-pulse
            ${theme === 'light' ? 'bg-yellow-500' : ''}
            ${theme === 'dark' ? 'bg-purple-600' : ''}
            ${theme === 'system' ? 'bg-blue-500' : ''}
          `} />
        </div>
      </div>
      
      {/* Theme Label */}
      <div className="text-xs font-medium text-gray-600 dark:text-gray-400 text-center min-w-0">
        <div className="truncate">{getThemeLabel()}</div>
      </div>
      
      {/* Theme Options Dots */}
      <div className="flex space-x-1">
        {['light', 'dark', 'system'].map((themeOption, index) => (
          <button
            key={themeOption}
            onClick={() => setTheme(themeOption as any)}
            className={`
              w-2 h-2 rounded-full transition-all duration-300
              ${theme === themeOption 
                ? 'bg-blue-500 scale-125 shadow-md' 
                : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
              }
              hover:scale-110 focus:outline-none focus:ring-2 focus:ring-blue-500/50
            `}
            title={`Switch to ${themeOption} theme`}
          />
        ))}
      </div>
    </div>
  );
};

export default ThemeToggle;