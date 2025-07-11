import React, { useState, FormEvent, ChangeEvent } from 'react';
import { Contact, ContactFormData } from '../types';
import { api } from '../utils/api';

interface ContactFormProps {
  contact?: Contact | null;
  onSave: () => void;
  onCancel: () => void;
}

const ContactForm: React.FC<ContactFormProps> = ({ contact, onSave, onCancel }) => {
  const [formData, setFormData] = useState<ContactFormData>({
    first_name: contact?.first_name || '',
    last_name: contact?.last_name || '',
    email: contact?.email || '',
    phone: contact?.phone || '',
    company: contact?.company || '',
    position: contact?.position || '',
    address: contact?.address || '',
    notes: contact?.notes || '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      if (contact?.id) {
        await api.updateContact(contact.id, formData);
      } else {
        await api.createContact(formData);
      }
      onSave();
    } catch (err) {
      console.error('Error saving contact:', err);
      setError('Failed to save contact. Please try again.');
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
      
      <div className="grid grid-cols-2 gap-4">
        <input
          type="text"
          name="first_name"
          placeholder="First Name"
          value={formData.first_name}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
          disabled={isSubmitting}
        />
        <input
          type="text"
          name="last_name"
          placeholder="Last Name"
          value={formData.last_name}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
          disabled={isSubmitting}
        />
      </div>
      
      <input
        type="email"
        name="email"
        placeholder="Email"
        value={formData.email}
        onChange={handleInputChange}
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        required
        disabled={isSubmitting}
      />
      
      <input
        type="text"
        name="phone"
        placeholder="Phone"
        value={formData.phone}
        onChange={handleInputChange}
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        disabled={isSubmitting}
      />
      
      <div className="grid grid-cols-2 gap-4">
        <input
          type="text"
          name="company"
          placeholder="Company"
          value={formData.company}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isSubmitting}
        />
        <input
          type="text"
          name="position"
          placeholder="Position"
          value={formData.position}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isSubmitting}
        />
      </div>
      
      <input
        type="text"
        name="address"
        placeholder="Address"
        value={formData.address}
        onChange={handleInputChange}
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        disabled={isSubmitting}
      />
      
      <textarea
        name="notes"
        placeholder="Notes"
        value={formData.notes}
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
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-md hover:shadow-lg"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : (contact?.id ? 'Update' : 'Create')} Contact
        </button>
      </div>
    </form>
  );
};

export default ContactForm;
