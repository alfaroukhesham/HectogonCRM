import React from 'react';
import Card from './Card';

interface ActivityItem {
  id: string;
  type: 'contact' | 'deal' | 'activity';
  title: string;
  description: string;
  time: string;
  user?: string;
}

interface RecentActivityProps {
  activities: ActivityItem[];
}

const RecentActivity: React.FC<RecentActivityProps> = ({ activities }) => {
  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'contact':
        return '👤';
      case 'deal':
        return '💰';
      case 'activity':
        return '📋';
      default:
        return '📝';
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'contact':
        return 'bg-blue-500';
      case 'deal':
        return 'bg-green-500';
      case 'activity':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          Recent Activity
        </h3>
        <button className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium">
          View all
        </button>
      </div>
      
      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div key={activity.id} className="flex items-start space-x-4 group">
            <div className={`
              w-8 h-8 rounded-full flex items-center justify-center text-white text-sm
              ${getActivityColor(activity.type)}
              group-hover:scale-110 transition-transform duration-200
            `}>
              {getActivityIcon(activity.type)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {activity.title}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 ml-2">
                  {activity.time}
                </p>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {activity.description}
              </p>
              {activity.user && (
                <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  by {activity.user}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {activities.length === 0 && (
        <div className="text-center py-8">
          <div className="text-4xl mb-2">📊</div>
          <p className="text-gray-500 dark:text-gray-400">No recent activity</p>
        </div>
      )}
    </Card>
  );
};

export default RecentActivity;