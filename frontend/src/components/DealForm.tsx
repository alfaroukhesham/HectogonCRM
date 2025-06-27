import React, { useState, FormEvent, ChangeEvent } from 'react';
import { Deal, DealFormData, Contact, DealStage } from '@/types';
import { dealsApi } from '@/utils/api';

interface DealFormProps {
  deal?: Deal | null;
  contacts: Contact[];
  onSave: () => void;
  onCancel: () => void;
}

const DealForm: React.FC<DealFormProps> = ({ deal, contacts, onSave, onCancel }) => {
  const [formData, setFormData] = useState<DealFormData>({
    title: deal?.title || '',
    contact_id: deal?.contact_id || '',
    value: deal?.value.toString() || '',
    stage: deal?.stage || 'Lead',
    probability: deal?.probability || 50,
    expected_close_date: deal?.expected_close_date || '',
    description: deal?.description || '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const stages: DealStage[] = ['Lead', 'Qualified', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost'];

  const handleInputChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleNumberChange = (e: ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    const numValue = name === 'probability' ? parseInt(value) || 0 : value;
    setFormData(prev => ({ ...prev, [name]: numValue }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const submitData = {
        title: formData.title,
        contact_id: formData.contact_id,
        value: parseFloat(formData.value) || 0,
        stage: formData.stage,
        probability: formData.probability,
        description: formData.description,
        ...(formData.expected_close_date && { expected_close_date: formData.expected_close_date }),
      };

      if (deal?.id) {
        await dealsApi.update(deal.id, submitData);
      } else {
        await dealsApi.create(submitData);
      }
      onSave();
    } catch (err) {
      console.error('Error saving deal:', err);
      setError('Failed to save deal. Please try again.');
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

      <input
        type="text"
        name="title"
        placeholder="Deal Title"
        value={formData.title}
        onChange={handleInputChange}
        className="w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        required
        disabled={isSubmitting}
      />

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
        <input
          type="number"
          name="value"
          placeholder="Deal Value"
          value={formData.value}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          required
          min="0"
          step="0.01"
          disabled={isSubmitting}
        />
        <select
          name="stage"
          value={formData.stage}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isSubmitting}
        >
          {stages.map((stage) => (
            <option key={stage} value={stage}>
              {stage}
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <input
          type="number"
          name="probability"
          min="0"
          max="100"
          placeholder="Probability %"
          value={formData.probability}
          onChange={handleNumberChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isSubmitting}
        />
        <input
          type="date"
          name="expected_close_date"
          placeholder="Expected Close Date"
          value={formData.expected_close_date}
          onChange={handleInputChange}
          className="border border-gray-300 dark:border-gray-600 rounded px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isSubmitting}
        />
      </div>

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
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 transition-colors shadow-md hover:shadow-lg"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving...' : (deal?.id ? 'Update' : 'Create')} Deal
        </button>
      </div>
    </form>
  );
};

export default DealForm;