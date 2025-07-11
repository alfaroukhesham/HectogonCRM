import React, { useState, useEffect } from 'react';
import { useOrganization } from '../hooks/useOrganization';
import { api } from '../utils/api';
import Card from '../components/ui/Card';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { Toast } from '../components/ui';
import { Organization, OrganizationUpdateRequest, OrganizationPlan } from '../types';

const OrganizationSettings: React.FC = () => {
  const { currentOrganization, userRole, refreshOrganizations } = useOrganization();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info' } | null>(null);
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
      setToast({ message: 'Organization settings updated successfully', type: 'success' });
      await refreshOrganizations();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update organization settings';
      setError(errorMessage);
      setToast({ message: errorMessage, type: 'error' });
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
      setToast({ message: 'Organization deleted successfully', type: 'success' });
      // The organization context will handle redirecting to another org or creating a new one
      await refreshOrganizations();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete organization';
      setError(errorMessage);
      setToast({ message: errorMessage, type: 'error' });
    } finally {
      setIsLoading(false);
      setShowDeleteDialog(false);
    }
  };

  if (!currentOrganization) {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Organization Settings</h1>
        </div>
        <Card className="p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Organization Selected</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Please select an organization to view and manage settings.
          </p>
        </Card>
      </div>
    );
  }

  if (userRole !== 'admin') {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Organization Settings</h1>
        </div>
        <Card className="p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Access Restricted</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You don't have permission to manage organization settings. Please contact an administrator.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Organization Settings</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage settings for {currentOrganization.name}
          </p>
        </div>
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

      {success && (
        <div className="bg-green-100 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-xl">
          <div className="flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>{success}</span>
          </div>
        </div>
      )}

      <div className="space-y-6">
        {/* Basic Information */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Basic Information
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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
                />
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

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
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

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={isLoading}
                className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-md hover:shadow-lg"
              >
                {isLoading ? (
                  <span className="flex items-center">
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Saving...
                  </span>
                ) : 'Save Changes'}
              </button>
            </div>
          </form>
        </Card>

        {/* Organization Plan */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            Subscription Plan
          </h2>
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10 rounded-xl p-6 border border-blue-100 dark:border-blue-800/30">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center">
                  <span className="text-lg font-bold text-gray-900 dark:text-white">
                    {currentOrganization.plan === OrganizationPlan.FREE && 'Free Plan'}
                    {currentOrganization.plan === OrganizationPlan.BASIC && 'Basic Plan'}
                    {currentOrganization.plan === OrganizationPlan.PREMIUM && 'Premium Plan'}
                    {currentOrganization.plan === OrganizationPlan.ENTERPRISE && 'Enterprise Plan'}
                  </span>
                  <span className="ml-2 px-2.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-medium rounded-full">
                    {currentOrganization.plan.toUpperCase()}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {currentOrganization.plan === OrganizationPlan.FREE && 'Basic features for small teams or individuals'}
                  {currentOrganization.plan === OrganizationPlan.BASIC && 'Enhanced features for growing teams'}
                  {currentOrganization.plan === OrganizationPlan.PREMIUM && 'Advanced features for professional teams'}
                  {currentOrganization.plan === OrganizationPlan.ENTERPRISE && 'Full-featured plan for large organizations'}
                </p>
              </div>
              <button
                onClick={() => {
                  // TODO: Open upgrade modal or redirect to billing
                }}
                className="px-4 py-2 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 text-sm font-medium"
              >
                Upgrade Plan
              </button>
            </div>
            
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Contacts</div>
                <div className="text-lg font-bold text-gray-900 dark:text-white">
                  {currentOrganization.plan === OrganizationPlan.FREE && 'Up to 100'}
                  {currentOrganization.plan === OrganizationPlan.BASIC && 'Up to 1,000'}
                  {currentOrganization.plan === OrganizationPlan.PREMIUM && 'Up to 10,000'}
                  {currentOrganization.plan === OrganizationPlan.ENTERPRISE && 'Unlimited'}
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Team Members</div>
                <div className="text-lg font-bold text-gray-900 dark:text-white">
                  {currentOrganization.plan === OrganizationPlan.FREE && 'Up to 3'}
                  {currentOrganization.plan === OrganizationPlan.BASIC && 'Up to 10'}
                  {currentOrganization.plan === OrganizationPlan.PREMIUM && 'Up to 25'}
                  {currentOrganization.plan === OrganizationPlan.ENTERPRISE && 'Unlimited'}
                </div>
              </div>
              <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Storage</div>
                <div className="text-lg font-bold text-gray-900 dark:text-white">
                  {currentOrganization.plan === OrganizationPlan.FREE && '1 GB'}
                  {currentOrganization.plan === OrganizationPlan.BASIC && '10 GB'}
                  {currentOrganization.plan === OrganizationPlan.PREMIUM && '100 GB'}
                  {currentOrganization.plan === OrganizationPlan.ENTERPRISE && 'Unlimited'}
                </div>
              </div>
            </div>
          </div>
        </Card>

        {/* Danger Zone */}
        <Card className="p-6 border-red-200 dark:border-red-800/30">
          <h2 className="text-lg font-semibold text-red-600 dark:text-red-400 mb-4 flex items-center">
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            Danger Zone
          </h2>
          <div className="bg-red-50 dark:bg-red-900/10 p-4 rounded-xl border border-red-200 dark:border-red-800/30">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-base font-semibold text-red-800 dark:text-red-400">Delete Organization</h3>
                <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                  Once you delete an organization, there is no going back. Please be certain.
                  All data associated with this organization will be permanently deleted.
                </p>
              </div>
              <button
                onClick={() => setShowDeleteDialog(true)}
                disabled={isLoading}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-sm rounded-lg shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Delete Organization
              </button>
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

export default OrganizationSettings;