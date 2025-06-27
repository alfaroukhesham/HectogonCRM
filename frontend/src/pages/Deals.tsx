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
      <div className="px-4 py-6 sm:px-0">
        <h2 className="text-2xl font-bold mb-6">Deals</h2>
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
        <h2 className="text-2xl font-bold">Deals</h2>
        <button
          onClick={() => setShowDealModal(true)}
          className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors"
        >
          Add Deal
        </button>
      </div>

      {/* Deals List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        {deals.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500">
            No deals found. Create your first deal!
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {deals.map((deal) => (
              <li key={deal.id}>
                <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      {deal.title}
                    </div>
                    <div className="text-sm text-gray-500">
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
                      className="text-blue-600 hover:text-blue-900 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onDealDelete(deal.id)}
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