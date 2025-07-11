import React, { useEffect, useState } from 'react';

interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  isVisible: boolean;
  onClose: () => void;
}

const Toast: React.FC<ToastProps> = ({
  message,
  type = 'info',
  duration = 4000,
  isVisible,
  onClose
}) => {
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setIsAnimating(true);
      const timer = setTimeout(() => {
        onClose();
      }, duration);

      return () => clearTimeout(timer);
    } else {
      setIsAnimating(false);
      return () => {}; // Return empty cleanup function
    }
  }, [isVisible, duration, onClose]);

  const getTypeStyles = () => {
    switch (type) {
      case 'success':
        return {
          bg: 'bg-green-500',
          icon: '✓',
          iconBg: 'bg-green-100 dark:bg-green-900/20',
          iconColor: 'text-green-600 dark:text-green-400'
        };
      case 'error':
        return {
          bg: 'bg-red-500',
          icon: '✕',
          iconBg: 'bg-red-100 dark:bg-red-900/20',
          iconColor: 'text-red-600 dark:text-red-400'
        };
      case 'warning':
        return {
          bg: 'bg-yellow-500',
          icon: '⚠',
          iconBg: 'bg-yellow-100 dark:bg-yellow-900/20',
          iconColor: 'text-yellow-600 dark:text-yellow-400'
        };
      case 'info':
      default:
        return {
          bg: 'bg-blue-500',
          icon: 'ℹ',
          iconBg: 'bg-blue-100 dark:bg-blue-900/20',
          iconColor: 'text-blue-600 dark:text-blue-400'
        };
    }
  };

  const styles = getTypeStyles();

  if (!isVisible && !isAnimating) return null;

  return (
    <div className="fixed top-4 right-4 z-50">
      <div
        className={`
          max-w-sm w-full bg-white dark:bg-gray-800 shadow-lg rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 overflow-hidden
          transform transition-all duration-300 ease-in-out
          ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
        `}
      >
        <div className="p-4">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${styles.iconBg}`}>
                <span className={`text-sm font-medium ${styles.iconColor}`}>
                  {styles.icon}
                </span>
              </div>
            </div>
            <div className="ml-3 w-0 flex-1 pt-0.5">
              <p className="text-sm font-medium text-gray-900 dark:text-white">
                {message}
              </p>
            </div>
            <div className="ml-4 flex-shrink-0 flex">
              <button
                className="bg-white dark:bg-gray-800 rounded-md inline-flex text-gray-400 dark:text-gray-500 hover:text-gray-500 dark:hover:text-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                onClick={onClose}
              >
                <span className="sr-only">Close</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        <div 
          className={`h-1 ${styles.bg} transform origin-left transition-transform ease-linear ${isVisible ? 'scale-x-0' : 'scale-x-100'}`}
          style={{ transitionDuration: `${duration}ms` }}
        />
      </div>
    </div>
  );
};

export default Toast; 
 
 
 
