import React, { useState, useEffect, useRef } from 'react';
import { Contact } from '../types';
import { getFullName, getInitials } from '../utils/formatters';
import Modal from '../components/Modal';
import ContactForm from '../components/ContactForm';
import { ConfirmDialog, Toast } from '../components/ui';
import { api } from '../utils/api';
import { useOrganization } from '../hooks/useOrganization';

const Contacts: React.FC = () => {
  const { currentOrganization, isLoading: orgLoading, error: orgError, retryLoading } = useOrganization();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [showContactModal, setShowContactModal] = useState<boolean>(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [contactToDelete, setContactToDelete] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info' } | null>(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // Load data when organization context is ready
  useEffect(() => {
    if (currentOrganization && !orgLoading && isMountedRef.current) {
      loadContacts();
    }
  }, [currentOrganization, orgLoading]);

  const loadContacts = async () => {
    try {
      if (!isMountedRef.current) return;
      
      setIsLoading(true);
      setError(null);
      console.log('Loading contacts...');
      const data = await api.getContacts();
      console.log('Contacts loaded:', data);
      
      if (!isMountedRef.current) {
        console.log('Component unmounted, skipping state update');
        return;
      }
      
      setContacts(data);
      console.log('Contacts state updated');
    } catch (error) {
      console.error('Error loading contacts:', error);
      if (isMountedRef.current) {
        setError('Failed to load contacts');
      }
    } finally {
      // Always set loading to false, regardless of mount state
      // This prevents getting stuck in loading state
      setIsLoading(false);
      console.log('Loading set to false');
    }
  };

  const handleContactSave = async () => {
    setShowContactModal(false);
    setEditingContact(null);
    await loadContacts(); // Reload contacts after save
    setToast({ message: 'Contact saved successfully!', type: 'success' });
  };

  const handleDeleteClick = (id: string) => {
    setContactToDelete(id);
    setShowConfirmDialog(true);
  };

  const handleConfirmDelete = async () => {
    if (!contactToDelete) return;
    
    try {
      await api.deleteContact(contactToDelete);
      await loadContacts(); // Reload contacts after delete
      setToast({ message: 'Contact deleted successfully!', type: 'success' });
    } catch (error) {
      console.error('Error deleting contact:', error);
      setToast({ message: 'Failed to delete contact. Please try again.', type: 'error' });
    } finally {
      setContactToDelete(null);
    }
  };

  const handleCancelDelete = () => {
    setContactToDelete(null);
    setShowConfirmDialog(false);
  };

  const filteredContacts = contacts.filter(contact => 
    contact.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    contact.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (contact.company || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Show loading while organization context is being loaded OR data is being fetched
  if (orgLoading || isLoading) {
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

  // Show error message if organization loading failed
  if (orgError) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Contacts</h2>
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
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Contacts</h2>
        <div className="text-center py-12">
          <p className="text-gray-600 dark:text-gray-400 mb-4">No organization selected</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">Please select an organization to view contacts.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Contacts</h2>
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-md">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={loadContacts}
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
                      onClick={() => handleDeleteClick(contact.id)}
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

      {/* Contact Modal */}
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

      {/* Confirm Delete Dialog */}
      <ConfirmDialog
        isOpen={showConfirmDialog}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        title="Delete Contact"
        message="Are you sure you want to delete this contact? This action cannot be undone."
        confirmText="Delete"
        cancelText="Cancel"
        variant="danger"
      />

      {/* Toast Notifications */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          isVisible={!!toast}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default Contacts;
