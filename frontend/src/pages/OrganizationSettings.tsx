import React, { useState, useEffect } from 'react';
import { useOrganization } from '../hooks/useOrganization';
import { api } from '../utils/api';
import Card from '../components/ui/Card';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { Organization, OrganizationUpdateRequest, OrganizationPlan } from '../types';

const OrganizationSettings: React.FC = () => {
  const { currentOrganization, userRole, refreshOrganizations } = useOrganization();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [formData, setFormData] = useState<OrganizationUpdateRequest>({
    name: '',
    description: '',
    website: '',
    industry: '',
    size: '',
  });

  useEffect(() => {
    if (currentOrganization) {
      setFormData({
        name: currentOrganization.name,
        description: currentOrganization.description || '',
        website: currentOrganization.website || '',
        industry: currentOrganization.industry || '',
        size: currentOrganization.size || '',
      });
    }
  }, [currentOrganization]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrganization) return;

    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      await api.updateOrganization(currentOrganization.id, formData);
      setSuccess('Organization settings updated successfully');
      await refreshOrganizations();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update organization settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteOrganization = async () => {
    if (!currentOrganization) return;

    setIsLoading(true);
    setError(null);

    try {
      await api.deleteOrganization(currentOrganization.id);
      // The organization context will handle redirecting to another org or creating a new one
      await refreshOrganizations();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete organization');
    } finally {
      setIsLoading(false);
    }
  };

  if (!currentOrganization) {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">
          No organization selected
        </div>
      </div>
    );
  }

  if (userRole !== 'admin') {
    return (
      <div className="p-6">
        <div className="text-center text-gray-500">
          You don't have permission to manage organization settings
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Organization Settings</h1>
        <p className="text-gray-600 mt-1">
          Manage settings for {currentOrganization.name}
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-700">{success}</p>
        </div>
      )}

      <div className="space-y-6">
        {/* Basic Information */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Basic Information</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                />
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        </Card>

        {/* Organization Plan */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Subscription Plan</h2>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-900">
                Current Plan: {currentOrganization.plan.toUpperCase()}
              </p>
              <p className="text-sm text-gray-500">
                {currentOrganization.plan === OrganizationPlan.FREE && 'Free plan with basic features'}
                {currentOrganization.plan === OrganizationPlan.BASIC && 'Basic plan with enhanced features'}
                {currentOrganization.plan === OrganizationPlan.PREMIUM && 'Premium plan with advanced features'}
                {currentOrganization.plan === OrganizationPlan.ENTERPRISE && 'Enterprise plan with full features'}
              </p>
            </div>
            <button
              onClick={() => {
                // TODO: Open upgrade modal or redirect to billing
              }}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors"
            >
              Upgrade Plan
            </button>
          </div>
        </Card>

        {/* Danger Zone */}
        <Card className="p-6 border-red-200">
          <h2 className="text-lg font-semibold text-red-900 mb-4">Danger Zone</h2>
          <div className="bg-red-50 p-4 rounded-md">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3 flex-1">
                <h3 className="text-sm font-medium text-red-800">Delete Organization</h3>
                <p className="mt-1 text-sm text-red-700">
                  Once you delete an organization, there is no going back. Please be certain.
                  All data associated with this organization will be permanently deleted.
                </p>
                <div className="mt-4">
                  <button
                    onClick={() => setShowDeleteDialog(true)}
                    disabled={isLoading}
                    className="px-4 py-2 bg-red-600 text-white text-sm rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Delete Organization
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        isOpen={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
        onConfirm={handleDeleteOrganization}
        title="Delete Organization"
        message={`Are you sure you want to delete "${currentOrganization?.name}"? This action cannot be undone and will permanently delete the organization and all its data.`}
        confirmText="Delete Organization"
        cancelText="Cancel"
        variant="danger"
      />
    </div>
  );
};

export default OrganizationSettings; 
