import React, { useState, useEffect } from 'react';
import { useOrganization } from '../hooks/useOrganization';
import { useAuth } from '../hooks/useAuth';
import { api } from '../utils/api';
import Card from '../components/ui/Card';
import Modal from '../components/Modal';
import { ConfirmDialog, Toast } from '../components/ui';
import { Invitation, InvitationCreateRequest, MembershipRole } from '../types';

const Invitations: React.FC = () => {
  const { currentOrganization, userRole } = useOrganization();
  const { user } = useAuth();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [inviteToRevoke, setInviteToRevoke] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info' } | null>(null);
  const [formData, setFormData] = useState<InvitationCreateRequest>({
    organization_id: '',
    email: '',
    role: MembershipRole.VIEWER,
  });

  const loadInvitations = async () => {
    if (!currentOrganization) return;

    try {
      setIsLoading(true);
      setError(null);
      const invitationsData = await api.getInvitations(currentOrganization.id);
      setInvitations(invitationsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load invitations');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateInvitation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentOrganization) return;

    setCreateLoading(true);
    try {
      await api.createInvitation({
        ...formData,
        organization_id: currentOrganization.id,
      });
      setIsCreateModalOpen(false);
      setFormData({
        organization_id: '',
        email: '',
        role: MembershipRole.VIEWER,
      });
      await loadInvitations();
      setToast({ message: 'Invitation sent successfully', type: 'success' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create invitation');
      setToast({ message: 'Failed to send invitation', type: 'error' });
    } finally {
      setCreateLoading(false);
    }
  };

  const handleResendInvite = async (inviteId: string) => {
    try {
      await api.resendInvitation(inviteId);
      setToast({ message: 'Invitation resent successfully', type: 'success' });
    } catch (err) {
      setToast({ message: 'Failed to resend invitation', type: 'error' });
    }
  };

  const handleRevokeInviteClick = (inviteId: string) => {
    setInviteToRevoke(inviteId);
    setShowConfirmDialog(true);
  };

  const handleRevokeInvite = async () => {
    if (!inviteToRevoke) return;

    try {
      await api.revokeInvitation(inviteToRevoke);
      await loadInvitations();
      setToast({ message: 'Invitation revoked successfully', type: 'success' });
    } catch (err) {
      setToast({ message: 'Failed to revoke invitation', type: 'error' });
    } finally {
      setInviteToRevoke(null);
      setShowConfirmDialog(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'accepted':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'expired':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
      case 'revoked':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const getRoleIcon = (role: MembershipRole) => {
    switch (role) {
      case MembershipRole.ADMIN:
        return '👑';
      case MembershipRole.EDITOR:
        return '✏️';
      case MembershipRole.VIEWER:
        return '👁️';
      default:
        return '👤';
    }
  };

  useEffect(() => {
    loadInvitations();
  }, [currentOrganization]);

  if (!currentOrganization) {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Invitations</h1>
        </div>
        <Card className="p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Organization Selected</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Please select an organization to view and manage invitations.
          </p>
        </Card>
      </div>
    );
  }

  if (userRole !== 'admin') {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Invitations</h1>
        </div>
        <Card className="p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Access Restricted</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You don't have permission to manage invitations. Please contact an administrator.
          </p>
        </Card>
      </div>
    );
  }

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
        <Card className="overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 animate-pulse">
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-32"></div>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {[1, 2, 3].map((i) => (
              <div key={i} className="px-6 py-4 flex items-center justify-between animate-pulse">
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700"></div>
                  <div>
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-2"></div>
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-48"></div>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-20 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  <div className="w-16 h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Invitations</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage invitations for {currentOrganization.name}
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-2.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 font-medium flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span>Send Invitation</span>
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

      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white flex items-center">
            <span>Sent Invitations</span>
            <span className="ml-2 px-2.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-medium rounded-full">
              {invitations.length}
            </span>
          </h3>
        </div>

        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {invitations.map((invitation) => (
            <div key={invitation.id} className="px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-semibold shadow-md">
                  {invitation.email.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{invitation.email}</p>
                  <div className="flex items-center mt-1">
                    <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
                      {getRoleIcon(invitation.role)} {invitation.role}
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    Sent {new Date(invitation.created_at).toLocaleDateString()}
                    {invitation.expires_at && (
                      <> • Expires {new Date(invitation.expires_at).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3 ml-14 sm:ml-0">
                <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${getStatusColor(invitation.status)}`}>
                  {invitation.status}
                </span>
                
                {invitation.status === 'pending' && (
                  <>
                    <button
                      onClick={() => handleResendInvite(invitation.id)}
                      className="px-3 py-1.5 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg text-sm transition-colors"
                    >
                      Resend
                    </button>
                    <button
                      onClick={() => handleRevokeInviteClick(invitation.id)}
                      className="px-3 py-1.5 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-sm transition-colors"
                    >
                      Revoke
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}

          {invitations.length === 0 && (
            <div className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
              <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">No invitations sent yet</p>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Invite team members to collaborate in your organization.
              </p>
              <button
                onClick={() => setIsCreateModalOpen(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Send First Invitation
              </button>
            </div>
          )}
        </div>
      </Card>

      {/* Create Invitation Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Send Invitation"
      >
        <form onSubmit={handleCreateInvitation} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              placeholder="Enter email address"
            />
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Role *
            </label>
            <select
              id="role"
              required
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as MembershipRole })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            >
              <option value={MembershipRole.VIEWER}>👁️ Viewer - Can view data</option>
              <option value={MembershipRole.EDITOR}>✏️ Editor - Can edit data</option>
              <option value={MembershipRole.ADMIN}>👑 Admin - Full access</option>
            </select>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg border border-blue-100 dark:border-blue-800">
            <p className="text-sm text-blue-700 dark:text-blue-400 flex items-center">
              <svg className="w-5 h-5 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>The invited user will receive an email with a link to join your organization.</span>
            </p>
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
                  Sending...
                </span>
              ) : 'Send Invitation'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Confirm Revoke Dialog */}
      <ConfirmDialog
        isOpen={showConfirmDialog}
        onClose={() => {
          setShowConfirmDialog(false);
          setInviteToRevoke(null);
        }}
        onConfirm={handleRevokeInvite}
        title="Revoke Invitation"
        message="Are you sure you want to revoke this invitation? The recipient will no longer be able to join your organization using this invite."
        confirmText="Revoke"
        cancelText="Cancel"
        variant="warning"
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

export default Invitations;