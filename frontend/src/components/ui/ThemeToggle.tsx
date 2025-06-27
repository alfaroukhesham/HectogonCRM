import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '@/hooks/useTheme';

const ThemeToggle: React.FC = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const themes = [
    { value: 'light', label: 'Light', icon: '☀️' },
    { value: 'dark', label: 'Dark', icon: '🌙' },
    { value: 'system', label: 'System', icon: '💻' }
  ] as const;

  const currentTheme = themes.find(t => t.value === theme) || themes[0];

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`
          flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium 
          transition-all duration-200 hover:scale-105
          bg-white dark:bg-gray-800 
          border border-gray-200 dark:border-gray-700
          text-gray-700 dark:text-gray-300
          hover:bg-gray-50 dark:hover:bg-gray-700
          shadow-sm hover:shadow-md
          ${isOpen ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}
        `}
        title="Change theme"
      >
        <span className="text-base">{currentTheme.icon}</span>
        <span className="hidden sm:inline">{currentTheme.label}</span>
        <svg 
          className={`w-4 h-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-1 z-50 animate-scale-in">
          {themes.map((themeOption) => (
            <button
              key={themeOption.value}
              onClick={() => {
                setTheme(themeOption.value);
                setIsOpen(false);
              }}
              className={`
                w-full flex items-center space-x-3 px-4 py-2 text-sm transition-colors duration-150
                ${theme === themeOption.value
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                }
              `}
            >
              <span className="text-base">{themeOption.icon}</span>
              <div className="flex-1 text-left">
                <div className="font-medium">{themeOption.label}</div>
                {themeOption.value === 'system' && (
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    Currently {resolvedTheme}
                  </div>
                )}
              </div>
              {theme === themeOption.value && (
                <svg className="w-4 h-4 text-blue-600 dark:text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
      
      {/* Current theme indicator */}
      <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-blue-500 flex items-center justify-center">
        <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
      </div>
    </div>
  );
};

export default ThemeToggle;