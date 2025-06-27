import React, { useState } from 'react';
import { Activity, Contact } from '@/types';
import { formatDate, getPriorityColor } from '@/utils/formatters';
import Modal from '@/components/Modal';
import ActivityForm from '@/components/ActivityForm';

interface ActivitiesProps {
  activities: Activity[];
  contacts: Contact[];
  onActivitySave: () => void;
  onActivityDelete: (id: string) => void;
  isLoading: boolean;
}

const Activities: React.FC<ActivitiesProps> = ({ 
  activities, 
  contacts, 
  onActivitySave, 
  onActivityDelete, 
  isLoading 
}) => {
  const [showActivityModal, setShowActivityModal] = useState<boolean>(false);
  const [editingActivity, setEditingActivity] = useState<Activity | null>(null);

  const getContactName = (contactId: string): string => {
    const contact = contacts.find(c => c.id === contactId);
    return contact ? `${contact.first_name} ${contact.last_name}` : 'Unknown Contact';
  };

  const handleActivitySave = () => {
    setShowActivityModal(false);
    setEditingActivity(null);
    onActivitySave();
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Activities</h2>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-gray-200 dark:bg-gray-700 h-20 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Activities</h2>
        <button
          onClick={() => setShowActivityModal(true)}
          className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-md transition-colors shadow-md hover:shadow-lg"
        >
          Add Activity
        </button>
      </div>

      {/* Activities List */}
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
        {activities.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
            No activities found. Create your first activity!
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {activities.map((activity) => (
              <li key={activity.id}>
                <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {activity.title}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {getContactName(activity.contact_id)} • {activity.type}
                      {activity.due_date && ` • Due: ${formatDate(activity.due_date)}`}
                    </div>
                    <div className="mt-1 flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(activity.priority)}`}>
                        {activity.priority}
                      </span>
                      {activity.completed && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                          Completed
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setEditingActivity(activity);
                        setShowActivityModal(true);
                      }}
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onActivityDelete(activity.id)}
                      className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Modal */}
      <Modal
        isOpen={showActivityModal}
        onClose={() => {
          setShowActivityModal(false);
          setEditingActivity(null);
        }}
        title={editingActivity ? 'Edit Activity' : 'Add Activity'}
      >
        <ActivityForm
          activity={editingActivity}
          contacts={contacts}
          onSave={handleActivitySave}
          onCancel={() => {
            setShowActivityModal(false);
            setEditingActivity(null);
          }}
        />
      </Modal>
    </div>
  );
};

export default Activities;