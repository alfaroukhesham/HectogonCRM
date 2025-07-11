import React from 'react';
import Card from './Card';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease';
  };
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'purple' | 'orange' | 'pink' | 'indigo';
  trend?: number[];
}

const StatCard: React.FC<StatCardProps> = ({ 
  title, 
  value, 
  change, 
  icon, 
  color,
  trend 
}) => {
  const colorClasses = {
    blue: 'from-blue-500 to-blue-600 text-blue-600 bg-blue-50 dark:bg-blue-500/10',
    green: 'from-green-500 to-green-600 text-green-600 bg-green-50 dark:bg-green-500/10',
    purple: 'from-purple-500 to-purple-600 text-purple-600 bg-purple-50 dark:bg-purple-500/10',
    orange: 'from-orange-500 to-orange-600 text-orange-600 bg-orange-50 dark:bg-orange-500/10',
    pink: 'from-pink-500 to-pink-600 text-pink-600 bg-pink-50 dark:bg-pink-500/10',
    indigo: 'from-indigo-500 to-indigo-600 text-indigo-600 bg-indigo-50 dark:bg-indigo-500/10',
  };

  return (
    <Card hover className="p-6 relative overflow-hidden group bg-gradient-to-br from-white to-gray-50/50 dark:from-gray-800 dark:to-gray-900/50">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-3 dark:opacity-5">
        <div className="absolute inset-0 bg-gradient-to-br from-transparent via-current to-transparent transform rotate-12 scale-150"></div>
      </div>
      
      <div className="relative">
        <div className="flex items-center justify-between mb-4">
          <div className={`
            w-12 h-12 rounded-xl flex items-center justify-center
            bg-gradient-to-br ${colorClasses[color].split(' ')[0]} ${colorClasses[color].split(' ')[1]}
            shadow-lg
            group-hover:scale-110 transition-transform duration-300
          `}>
            <div className="text-white text-xl">
              {icon}
            </div>
          </div>
          
          {change && (
            <div className={`
              flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium
              ${change.type === 'increase' 
                ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400' 
                : 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
              }
            `}>
              <span>{change.type === 'increase' ? '↗' : '↘'}</span>
              <span>{Math.abs(change.value)}%</span>
            </div>
          )}
        </div>
        
        <div className="space-y-1">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 group-hover:text-gray-700 dark:group-hover:text-gray-300 transition-colors">
            {title}
          </p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white group-hover:scale-105 transition-transform duration-300 origin-left">
            {value}
          </p>
        </div>
        
        {/* Mini Trend Line */}
        {trend && (
          <div className="mt-4 h-8 flex items-end space-x-1">
            {trend.map((height, index) => (
              <div
                key={index}
                className={`
                  w-1 rounded-full bg-gradient-to-t ${colorClasses[color].split(' ')[0]} ${colorClasses[color].split(' ')[1]}
                  opacity-60 group-hover:opacity-100 transition-opacity duration-300
                `}
                style={{ height: `${(height / Math.max(...trend)) * 100}%` }}
              />
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};

export default StatCard;
