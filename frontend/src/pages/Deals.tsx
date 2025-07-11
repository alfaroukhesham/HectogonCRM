import React, { useState, useEffect } from 'react';
import { Deal, Contact } from '../types';
import { formatCurrency, getStageColor } from '../utils/formatters';
import Modal from '../components/Modal';
import DealForm from '../components/DealForm';
import { api } from '../utils/api';
import { useOrganization } from '../hooks/useOrganization';

const Deals: React.FC = () => {
  const { currentOrganization, isLoading: orgLoading, error: orgError, retryLoading } = useOrganization();
  const [deals, setDeals] = useState<Deal[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [showDealModal, setShowDealModal] = useState<boolean>(false);
  const [editingDeal, setEditingDeal] = useState<Deal | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load data when organization context is ready
  useEffect(() => {
    if (currentOrganization && !orgLoading) {
      loadData();
    }
  }, [currentOrganization, orgLoading]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [dealsData, contactsData] = await Promise.all([
        api.getDeals(),
        api.getContacts()
      ]);
      setDeals(dealsData);
      setContacts(contactsData);
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Failed to load deals and contacts');
    } finally {
      setIsLoading(false);
    }
  };

  const getContactName = (contactId: string): string => {
    const contact = contacts.find(c => c.id === contactId);
    return contact ? `${contact.first_name} ${contact.last_name}` : 'Unknown Contact';
  };

  const handleDealSave = async () => {
    setShowDealModal(false);
    setEditingDeal(null);
    await loadData(); // Reload data after save
  };

  const handleDealDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this deal?')) return;
    
    try {
      await api.deleteDeal(id);
      await loadData(); // Reload data after delete
    } catch (error) {
      console.error('Error deleting deal:', error);
      alert('Failed to delete deal');
    }
  };

  // Show loading while organization context is being loaded OR data is being fetched
  if (orgLoading || isLoading) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Deals</h2>
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
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Deals</h2>
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
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Deals</h2>
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400 mb-4">No organization selected</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">Please select an organization to view deals.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Deals</h2>
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
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Deals</h2>
        <button
          onClick={() => setShowDealModal(true)}
          className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md transition-colors shadow-md hover:shadow-lg"
        >
          Add Deal
        </button>
      </div>

      {/* Deals List */}
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
        {deals.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
            No deals found. Create your first deal!
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {deals.map((deal) => (
              <li key={deal.id}>
                <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-white">
                      {deal.title}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {getContactName(deal.contact_id)} • {formatCurrency(deal.value)}
                    </div>
                    <div className="mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStageColor(deal.stage)}`}>
                        {deal.stage}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setEditingDeal(deal);
                        setShowDealModal(true);
                      }}
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDealDelete(deal.id)}
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
        isOpen={showDealModal}
        onClose={() => {
          setShowDealModal(false);
          setEditingDeal(null);
        }}
        title={editingDeal ? 'Edit Deal' : 'Add Deal'}
      >
        <DealForm
          deal={editingDeal}
          contacts={contacts}
          onSave={handleDealSave}
          onCancel={() => {
            setShowDealModal(false);
            setEditingDeal(null);
          }}
        />
      </Modal>
    </div>
  );
};

export default Deals;
