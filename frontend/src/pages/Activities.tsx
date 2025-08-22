import React, { useState, useEffect, useRef } from 'react';
import { Activity, Contact } from '../types';
import { formatDate, getPriorityColor } from '../utils/formatters';
import Modal from '../components/Modal';
import ActivityForm from '../components/ActivityForm';
import { api } from '../utils/api';
import { useOrganization } from '../hooks/useOrganization';

const Activities: React.FC = () => {
  const { currentOrganization, isLoading: orgLoading, error: orgError, retryLoading } = useOrganization();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [showActivityModal, setShowActivityModal] = useState<boolean>(false);
  const [editingActivity, setEditingActivity] = useState<Activity | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Tracks "latest" request; increment to invalidate older responses
  const requestIdRef = useRef(0);

  // Load data when organization context is ready
  useEffect(() => {
    if (!currentOrganization || orgLoading) return;
    // Kick off a load; cleanup invalidates any in-flight request
    loadData();
    return () => {
      // Invalidate pending request to prevent state updates after unmount/org switch
      requestIdRef.current++;
    };
  }, [currentOrganization?.id, orgLoading]);

  const loadData = async () => {
    // Capture a unique id for this request
    const requestId = ++requestIdRef.current;
    try {
      setIsLoading(true);
      setError(null);
      const [activitiesData, contactsData] = await Promise.all([
        api.getActivities(),
        api.getContacts()
      ]);
      
      // Ignore out-of-date responses
      if (requestId !== requestIdRef.current) return;
      setActivities(activitiesData);
      setContacts(contactsData);
    } catch (err) {
      // Ignore errors from invalidated requests
      if (requestId !== requestIdRef.current) return;
      console.error('Error loading data:', err);
      setError('Failed to load activities and contacts');
    } finally {
      // Only clear loading for the latest request
      if (requestId === requestIdRef.current) {
        setIsLoading(false);
      }
    }
  };

  const getContactName = (contactId: string): string => {
    const contact = contacts.find(c => c.id === contactId);
    return contact ? `${contact.first_name} ${contact.last_name}` : 'Unknown Contact';
  };

  const handleActivitySave = async () => {
    setShowActivityModal(false);
    setEditingActivity(null);
    await loadData(); // Reload data after save
  };

  const handleActivityDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this activity?')) return;
    
    try {
      await api.deleteActivity(id);
      await loadData(); // Reload data after delete
    } catch (error) {
      console.error('Error deleting activity:', error);
      alert('Failed to delete activity');
    }
  };

  // Show loading while organization context is being loaded OR data is being fetched
  if (orgLoading || isLoading) {
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

  // Show error message if organization loading failed
  if (orgError) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Activities</h2>
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400 mb-4">Organization Loading Failed</p>
          <p className="text-sm text-gray-500 dark:text-gray-500 mb-6">{orgError}</p>
          <button
            onClick={retryLoading}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Show message if no organization is selected
  if (!currentOrganization) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Activities</h2>
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400 mb-4">No organization selected</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">Please select an organization to view activities.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Activities</h2>
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-md">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={loadData}
              className="text-red-700 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 ml-4"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Activities</h2>
        <button
          onClick={() => setShowActivityModal(true)}
          className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white px-6 py-2.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 font-medium"
        >
          <span className="flex items-center space-x-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span>
          Add Activity
            </span>
          </span>
        </button>
      </div>

      {/* Activities List */}
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700">
        {activities.length === 0 ? (
          <div className="px-4 py-12 text-center text-gray-500 dark:text-gray-400">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
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
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 transition-colors px-3 py-1 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleActivityDelete(activity.id)}
                      className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 transition-colors px-3 py-1 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20"
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
