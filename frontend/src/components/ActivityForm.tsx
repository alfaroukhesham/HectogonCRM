import React, { useState, FormEvent, ChangeEvent } from 'react';
import { Activity, ActivityFormData, Contact, ActivityType, ActivityPriority } from '@/types';
import { activitiesApi } from '@/utils/api';

interface ActivityFormProps {
  activity?: Activity | null;
  contacts: Contact[];
  onSave: () => void;
  onCancel: () => void;
}

const ActivityForm: React.FC<ActivityFormProps> = ({ activity, contacts, onSave, onCancel }) => {
  const [formData, setFormData] = useState<ActivityFormData>({
    contact_id: activity?.contact_id || '',
    type: activity?.type || 'Note',
    title: activity?.title || '',
    description: activity?.description || '',
    due_date: activity?.due_date || '',
    priority: activity?.priority || 'Medium',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const types: ActivityType[] = ['Call', 'Email', 'Meeting', 'Note', 'Task'];
  const priorities: ActivityPriority[] = ['Low', 'Medium', 'High'];

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const submitData = {
        contact_id: formData.contact_id,
        type: formData.type,
        title: formData.title,
        description: formData.description,
        priority: formData.priority,
        ...(formData.due_date && { due_date: formData.due_date }),
      };

      if (activity?.id) {
        await activitiesApi.update(activity.id, submitData);
      } else {
        await activitiesApi.create(submitData);
      }
      onSave();
    } catch (err) {
      console.error('Error saving activity:', err);
      setError('Failed to save activity. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {error && (
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <select
        name="contact_id"
        value={formData.contact_id}
        onChange={handleInputChange}
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        required
        disabled={isSubmitting}
      >
        <option value="">Select Contact</option>
        {contacts.map((contact) => (
          <option key={contact.id} value={contact.id}>
            {contact.first_name} {contact.last_name} - {contact.company}
          </option>
        ))}
      </select>

      <div className="grid grid-cols-2 gap-4">
        <select
          name="type"
          value={formData.type}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isSubmitting}
        >
          {types.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <select
          name="priority"
          value={formData.priority}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isSubmitting}
        >
          {priorities.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </select>
      </div>

      <input
        type="text"
        name="title"
        placeholder="Activity Title"
        value={formData.title}
        onChange={handleInputChange}
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        required
        disabled={isSubmitting}
      />

      <input
        type="datetime-local"
        name="due_date"
        placeholder="Due Date"
        value={formData.due_date}
        onChange={handleInputChange}
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        disabled={isSubmitting}
      />

      <textarea
        name="description"
        placeholder="Description"
        value={formData.description}
        onChange={handleInputChange}
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-20"
        disabled={isSubmitting}
      />

      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 dark:text-gray-400 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
          disabled={isSubmitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 transition-colors shadow-md hover:shadow-lg"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : (activity?.id ? 'Update' : 'Create')} Activity
        </button>
      </div>
    </form>
  );
};

export default ActivityForm;