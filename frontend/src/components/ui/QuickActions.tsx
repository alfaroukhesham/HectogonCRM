import React from 'react';
import Card from './Card';

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  onClick: () => void;
}

interface QuickActionsProps {
  actions: QuickAction[];
}

const QuickActions: React.FC<QuickActionsProps> = ({ actions }) => {
  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
        Quick Actions
      </h3>
      
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action) => (
          <button
            key={action.id}
            onClick={action.onClick}
            className={`
              p-4 rounded-xl text-left transition-all duration-200
              hover:scale-105 hover:shadow-lg
              bg-gradient-to-br ${action.color}
              group
            `}
          >
            <div className="text-2xl mb-2 group-hover:scale-110 transition-transform duration-200">
              {action.icon}
            </div>
            <h4 className="font-semibold text-white text-sm mb-1">
              {action.title}
            </h4>
            <p className="text-white/80 text-xs">
              {action.description}
            </p>
          </button>
        ))}
      </div>
    </Card>
  );
};

export default QuickActions;