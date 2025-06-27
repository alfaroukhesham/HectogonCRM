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
      <div className="px-4 py-6 sm:px-0">
        <h2 className="text-2xl font-bold mb-6">Activities</h2>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-gray-200 h-20 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Activities</h2>
        <button
          onClick={() => setShowActivityModal(true)}
          className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors"
        >
          Add Activity
        </button>
      </div>

      {/* Activities List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        {activities.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500">
            No activities found. Create your first activity!
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {activities.map((activity) => (
              <li key={activity.id}>
                <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {activity.title}
                    </div>
                    <div className="text-sm text-gray-500">
                      {getContactName(activity.contact_id)} • {activity.type}
                      {activity.due_date && ` • Due: ${formatDate(activity.due_date)}`}
                    </div>
                    <div className="mt-1 flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(activity.priority)}`}>
                        {activity.priority}
                      </span>
                      {activity.completed && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
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
                      className="text-blue-600 hover:text-blue-900 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onActivityDelete(activity.id)}
                      className="text-red-600 hover:text-red-900 transition-colors"
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