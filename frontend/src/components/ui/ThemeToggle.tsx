import React from 'react';
import { useTheme } from '@/hooks/useTheme';

const ThemeToggle: React.FC = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();

  const themes = [
    { value: 'light', label: 'Light', icon: '☀️' },
    { value: 'dark', label: 'Dark', icon: '🌙' },
    { value: 'system', label: 'System', icon: '💻' }
  ] as const;

  return (
    <div className="relative">
      <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1 transition-colors duration-200">
        {themes.map((themeOption) => (
          <button
            key={themeOption.value}
            onClick={() => setTheme(themeOption.value)}
            className={`
              flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-all duration-200
              ${theme === themeOption.value
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }
            `}
            title={`Switch to ${themeOption.label.toLowerCase()} theme`}
          >
            <span className="text-base">{themeOption.icon}</span>
            <span className="hidden sm:inline">{themeOption.label}</span>
          </button>
        ))}
      </div>
      
      {/* Current theme indicator */}
      <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-blue-500 flex items-center justify-center">
        <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
      </div>
    </div>
  );
};

export default ThemeToggle;