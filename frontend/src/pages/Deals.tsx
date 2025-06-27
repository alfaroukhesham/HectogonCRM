import React, { useState } from 'react';
import { Deal, Contact } from '@/types';
import { formatCurrency, getStageColor } from '@/utils/formatters';
import Modal from '@/components/Modal';
import DealForm from '@/components/DealForm';

interface DealsProps {
  deals: Deal[];
  contacts: Contact[];
  onDealSave: () => void;
  onDealDelete: (id: string) => void;
  isLoading: boolean;
}

const Deals: React.FC<DealsProps> = ({ 
  deals, 
  contacts, 
  onDealSave, 
  onDealDelete, 
  isLoading 
}) => {
  const [showDealModal, setShowDealModal] = useState<boolean>(false);
  const [editingDeal, setEditingDeal] = useState<Deal | null>(null);

  const getContactName = (contactId: string): string => {
    const contact = contacts.find(c => c.id === contactId);
    return contact ? `${contact.first_name} ${contact.last_name}` : 'Unknown Contact';
  };

  const handleDealSave = () => {
    setShowDealModal(false);
    setEditingDeal(null);
    onDealSave();
  };

  if (isLoading) {
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
                      onClick={() => onDealDelete(deal.id)}
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