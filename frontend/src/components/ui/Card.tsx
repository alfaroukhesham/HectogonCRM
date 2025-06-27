import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  hover?: boolean;
  gradient?: boolean;
}

const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  hover = false,
  gradient = false 
}) => {
  return (
    <div className={`
      bg-white dark:bg-gray-800 
      rounded-xl 
      shadow-sm dark:shadow-gray-900/20
      border border-gray-200/60 dark:border-gray-700/60
      backdrop-blur-sm
      transition-all duration-300 ease-out
      ${hover ? 'hover:shadow-lg hover:shadow-gray-200/40 dark:hover:shadow-gray-900/40 hover:-translate-y-0.5' : ''}
      ${gradient ? 'bg-gradient-to-br from-white to-gray-50/50 dark:from-gray-800 dark:to-gray-900/50' : ''}
      ${className}
    `}>
      {children}
    </div>
  );
};

export default Card;