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
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Contacts</h2>
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-gray-200 dark:bg-gray-700 h-16 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Contacts</h2>
        <button
          onClick={() => setShowContactModal(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition-colors shadow-md hover:shadow-lg"
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
          className="w-full max-w-md border border-gray-300 dark:border-gray-600 rounded-md px-3 py-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 shadow-sm"
        />
      </div>

      {/* Contacts List */}
      <div className="bg-white dark:bg-gray-800 shadow-lg rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
        {filteredContacts.length === 0 ? (
          <div className="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
            {searchTerm ? 'No contacts match your search.' : 'No contacts found. Create your first contact!'}
          </div>
        ) : (
          <ul className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredContacts.map((contact) => (
              <li key={contact.id}>
                <div className="px-4 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <div className="flex items-center">
                    <div className="flex-shrink-0 h-10 w-10">
                      <div className="h-10 w-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                        <span className="text-blue-600 dark:text-blue-400 font-medium">
                          {getInitials(contact.first_name, contact.last_name)}
                        </span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {getFullName(contact.first_name, contact.last_name)}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
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
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => onContactDelete(contact.id)}
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