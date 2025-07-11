import React, { useState, useEffect } from 'react';
import { useOrganization } from '../hooks/useOrganization';
import { useAuth } from '../hooks/useAuth';
import { api } from '../utils/api';
import Card from '../components/ui/Card';
import Modal from '../components/Modal';
import { Invitation, InvitationCreateRequest, MembershipRole } from '../types';

const Invitations: React.FC = () => {
  const { currentOrganization, userRole } = useOrganization();
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create invitation');
    } finally {
      setCreateLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'accepted':
        return 'bg-green-100 text-green-800';
      case 'declined':
        return 'bg-red-100 text-red-800';
      case 'expired':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
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
          You don't have permission to manage invitations
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-gray-200 rounded-lg"></div>
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
          <h1 className="text-2xl font-bold text-gray-900">Invitations</h1>
          <p className="text-gray-600 mt-1">
            Manage invitations for {currentOrganization.name}
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
        >
          Send Invitation
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Sent Invitations ({invitations.length})
          </h3>
        </div>

        <div className="divide-y divide-gray-200">
          {invitations.map((invitation) => (
            <div key={invitation.id} className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className="w-10 h-10 rounded-full bg-gray-500 flex items-center justify-center text-white font-semibold">
                  {invitation.email.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">{invitation.email}</p>
                  <p className="text-sm text-gray-500">
                    {getRoleIcon(invitation.role)} {invitation.role}
                  </p>
                  <p className="text-xs text-gray-400">
                    Sent {new Date(invitation.created_at).toLocaleDateString()}
                    {invitation.expires_at && (
                      <> • Expires {new Date(invitation.expires_at).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(invitation.status)}`}>
                  {invitation.status}
                </span>
                
                {invitation.status === 'pending' && (
                  <button
                    onClick={() => {
                      // TODO: Resend invitation
                    }}
                    className="px-3 py-1 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-md text-sm transition-colors"
                  >
                    Resend
                  </button>
                )}
              </div>
            </div>
          ))}

          {invitations.length === 0 && (
            <div className="px-6 py-12 text-center text-gray-500">
              No invitations sent yet
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
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter email address"
            />
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
              Role *
            </label>
            <select
              id="role"
              required
              value={formData.role}
              onChange={(e) => setFormData({ ...formData, role: e.target.value as MembershipRole })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={MembershipRole.VIEWER}>👁️ Viewer - Can view data</option>
              <option value={MembershipRole.EDITOR}>✏️ Editor - Can edit data</option>
              <option value={MembershipRole.ADMIN}>👑 Admin - Full access</option>
            </select>
          </div>

          <div className="bg-blue-50 p-3 rounded-md">
            <p className="text-sm text-blue-700">
              The invited user will receive an email with a link to join your organization.
            </p>
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
              {createLoading ? 'Sending...' : 'Send Invitation'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};

export default Invitations; 
