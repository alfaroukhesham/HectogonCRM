import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useOrganization } from '../hooks/useOrganization';
import { useAuth } from '../hooks/useAuth';
import Card from '../components/ui/Card';
import Modal from '../components/Modal';
import { OrganizationCreateRequest, OrganizationPlan } from '../types';

const Organizations: React.FC = () => {
  const { organizations, currentOrganization, switchOrganization, createOrganization, isLoading } = useOrganization();
  const { user } = useAuth();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Organizations</h1>
          <p className="text-gray-600 mt-1">Manage your organizations and switch between them</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          Create Organization
        </button>
      </div>

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
                  <div className="w-12 h-12 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold text-lg">
                    {org.organization_name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{org.organization_name}</h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`px-2 py-1 text-xs rounded-full font-medium ${
                      org.role === 'admin' ? 'bg-purple-100 text-purple-700' :
                      org.role === 'editor' ? 'bg-blue-100 text-blue-700' :
                      'bg-gray-100 text-gray-700'
                    }`}>
                      {org.role === 'admin' && '👑 Admin'}
                      {org.role === 'editor' && '✏️ Editor'}
                      {org.role === 'viewer' && '👁️ Viewer'}
                    </span>
                    {currentOrganization?.id === org.organization_id && (
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full font-medium">
                        Current
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2 mb-4">
              <p className="text-sm text-gray-600">
                <span className="font-medium">Joined:</span> {' '}
                {new Date(org.joined_at).toLocaleDateString()}
              </p>
              {org.last_accessed && (
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Last accessed:</span> {' '}
                  {new Date(org.last_accessed).toLocaleDateString()}
                </p>
              )}
            </div>

            <div className="flex space-x-2">
              {currentOrganization?.id !== org.organization_id && (
                <button
                  onClick={() => switchOrganization(org.organization_id)}
                  className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                >
                  Switch to
                </button>
              )}
              {org.role === 'admin' && (
                <button
                  onClick={() => {
                    // TODO: Navigate to settings
                  }}
                  className="px-3 py-2 border border-gray-300 text-gray-700 text-sm rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
                >
                  Settings
                </button>
              )}
            </div>
          </Card>
        ))}
      </div>

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
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        <form onSubmit={handleCreateOrganization} className="space-y-4">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Organization Name *
            </label>
            <input
              type="text"
              id="name"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter organization name"
            />
          </div>

          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Describe your organization"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="industry" className="block text-sm font-medium text-gray-700 mb-1">
                Industry
              </label>
              <input
                type="text"
                id="industry"
                value={formData.industry || ''}
                onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., Technology"
              />
            </div>

            <div>
              <label htmlFor="size" className="block text-sm font-medium text-gray-700 mb-1">
                Company Size
              </label>
              <select
                id="size"
                value={formData.size || ''}
                onChange={(e) => setFormData({ ...formData, size: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
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
            <label htmlFor="website" className="block text-sm font-medium text-gray-700 mb-1">
              Website
            </label>
            <input
              type="url"
              id="website"
              value={formData.website || ''}
              onChange={(e) => setFormData({ ...formData, website: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="https://example.com"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={() => setIsCreateModalOpen(false)}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {createLoading ? 'Creating...' : 'Create Organization'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Organizations; 
