import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOrganization } from '../hooks/useOrganization';
import { useAuth } from '../hooks/useAuth';
import Card from '../components/ui/Card';
import Modal from '../components/Modal';
import { OrganizationCreateRequest, OrganizationPlan } from '../types';
import { Toast } from '../components/ui';

const Organizations: React.FC = () => {
  const navigate = useNavigate();
  const { organizations, currentOrganization, switchOrganization, createOrganization, isLoading } = useOrganization();
  const { user } = useAuth();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info' } | null>(null);
  const [formData, setFormData] = useState<OrganizationCreateRequest>({
    name: '',
    description: '',
    plan: OrganizationPlan.FREE,
    website: '',
    industry: '',
    size: '',
  });

  const handleCreateOrganization = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    setError(null);

    try {
      await createOrganization(formData);
      setIsCreateModalOpen(false);
      setFormData({
        name: '',
        description: '',
        plan: OrganizationPlan.FREE,
        website: '',
        industry: '',
        size: '',
      });
      setToast({ message: 'Organization created successfully!', type: 'success' });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create organization';
      setError(errorMessage);
      console.error('Failed to create organization:', error);
    } finally {
      setCreateLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-48 mb-2"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-64"></div>
          </div>
          <div className="h-10 w-40 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-64 bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Organizations</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your organizations and switch between them
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-2.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 font-medium flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          <span>Create Organization</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-xl">
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span>{error}</span>
          </div>
        </div>
      )}

      {organizations.length === 0 ? (
        <Card className="p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Organizations Yet</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
            Create your first organization to start managing your contacts, deals, and activities.
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-2.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 font-medium"
          >
            Create Your First Organization
          </button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {organizations.map((org) => (
            <Card key={org.organization_id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {org.organization_logo_url ? (
                    <img
                      src={org.organization_logo_url}
                      alt={org.organization_name}
                      className="w-12 h-12 rounded-full object-cover"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-md">
                      {org.organization_name.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{org.organization_name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                        org.role === 'admin' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400' :
                        org.role === 'editor' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                        'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                      }`}>
                        {org.role === 'admin' && '👑 Admin'}
                        {org.role === 'editor' && '✏️ Editor'}
                        {org.role === 'viewer' && '👁️ Viewer'}
                      </span>
                      {currentOrganization?.id === org.organization_id && (
                        <span className="px-2 py-1 text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full font-medium">
                          Current
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  <span className="font-medium">Joined:</span> {' '}
                  {new Date(org.joined_at).toLocaleDateString()}
                </p>
                {org.last_accessed && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    <span className="font-medium">Last accessed:</span> {' '}
                    {new Date(org.last_accessed).toLocaleDateString()}
                  </p>
                )}
              </div>

              <div className="flex space-x-2">
                {currentOrganization?.id !== org.organization_id && (
                  <button
                    onClick={() => switchOrganization(org.organization_id)}
                    className="flex-1 px-3 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-sm rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
                  >
                    Switch to
                  </button>
                )}
                {org.role === 'admin' && (
                  <button
                    onClick={() => navigate(`/settings`)}
                    className="px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    Settings
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Organization Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setError(null);
        }}
        title="Create New Organization"
      >
        {error && (
          <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}
        <form onSubmit={handleCreateOrganization} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Organization Name *
            </label>
            <input
              type="text"
              id="name"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Enter organization name"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Description
            </label>
            <textarea
              id="description"
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Describe your organization"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="industry" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Industry
              </label>
              <input
                type="text"
                id="industry"
                value={formData.industry || ''}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="e.g., Technology"
              />
            </div>

            <div>
              <label htmlFor="size" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Company Size
              </label>
              <select
                id="size"
                value={formData.size || ''}
                onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Select size</option>
                <option value="1-10">1-10 employees</option>
                <option value="11-50">11-50 employees</option>
                <option value="51-200">51-200 employees</option>
                <option value="201-500">201-500 employees</option>
                <option value="500+">500+ employees</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="website" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Website
            </label>
            <input
              type="url"
              id="website"
              value={formData.website || ''}
              onChange={(e) => setFormData({ ...formData, website: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="https://example.com"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(false)}
              className="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createLoading}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md hover:shadow-lg"
            >
              {createLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </span>
              ) : 'Create Organization'}
            </button>
          </div>
        </form>
      </Modal>

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

export default Organizations;