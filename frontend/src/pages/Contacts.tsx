import React, { useState } from 'react';
import { Contact } from '@/types';
import { getFullName, getInitials } from '@/utils/formatters';
import Modal from '@/components/Modal';
import ContactForm from '@/components/ContactForm';

interface ContactsProps {
  contacts: Contact[];
  onContactSave: () => void;
  onContactDelete: (id: string) => void;
  isLoading: boolean;
}

const Contacts: React.FC<ContactsProps> = ({ 
  contacts, 
  onContactSave, 
  onContactDelete, 
  isLoading 
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showContactModal, setShowContactModal] = useState<boolean>(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);

  const filteredContacts = contacts.filter(contact => 
    contact.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (contact.company || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleContactSave = () => {
    setShowContactModal(false);
    setEditingContact(null);
    onContactSave();
  };

  if (isLoading) {
    return (
      <div className="px-4 py-6 sm:px-0">
        <h2 className="text-2xl font-bold mb-6">Contacts</h2>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-gray-200 h-16 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold">Contacts</h2>
        <button
          onClick={() => setShowContactModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
        >
          Add Contact
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <input
          type="text"
          placeholder="Search contacts..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full max-w-md border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Contacts List */}
      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        {filteredContacts.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500">
            {searchTerm ? 'No contacts match your search.' : 'No contacts found. Create your first contact!'}
          </div>
        ) : (
          <ul className="divide-y divide-gray-200">
            {filteredContacts.map((contact) => (
              <li key={contact.id}>
                <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                        <span className="text-blue-600 font-medium">
                          {getInitials(contact.first_name, contact.last_name)}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900">
                        {getFullName(contact.first_name, contact.last_name)}
                      </div>
                      <div className="text-sm text-gray-500">
                        {contact.email} • {contact.company}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setEditingContact(contact);
                        setShowContactModal(true);
                      }}
                      className="text-blue-600 hover:text-blue-900 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onContactDelete(contact.id)}
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
        isOpen={showContactModal}
        onClose={() => {
          setShowContactModal(false);
          setEditingContact(null);
        }}
        title={editingContact ? 'Edit Contact' : 'Add Contact'}
      >
        <ContactForm
          contact={editingContact}
          onSave={handleContactSave}
          onCancel={() => {
            setShowContactModal(false);
            setEditingContact(null);
          }}
        />
      </Modal>
    </div>
  );
};

export default Contacts; 