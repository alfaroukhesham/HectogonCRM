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
      shadow-lg dark:shadow-xl
      shadow-gray-200/50 dark:shadow-gray-900/50
      border border-gray-200/60 dark:border-gray-700/60
      backdrop-blur-sm
      transition-all duration-300 ease-out
      ${hover ? 'hover:shadow-xl hover:shadow-gray-300/60 dark:hover:shadow-gray-900/60 hover:-translate-y-1 hover:scale-[1.02]' : ''}
      ${gradient ? 'bg-gradient-to-br from-white to-gray-50/50 dark:from-gray-800 dark:to-gray-900/50' : ''}
      ${className}
    `}>
      {children}
    </div>
  );
};

export default Card;