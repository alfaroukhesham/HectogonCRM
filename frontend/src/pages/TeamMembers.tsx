import React, { useState, useEffect } from 'react';
import { useOrganization } from '../hooks/useOrganization';
import { api } from '../utils/api';
import Card from '../components/ui/Card';
import { ConfirmDialog, Toast } from '../components/ui';
import { MembershipRole } from '../types';

interface TeamMember {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  user_avatar?: string;
  role: MembershipRole;
  status: string;
  joined_at: string;
  last_accessed?: string;
}

const TeamMembers: React.FC = () => {
  const { currentOrganization, userRole } = useOrganization();
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'warning' | 'info' } | null>(null);

  const loadMembers = async () => {
    if (!currentOrganization) return;

    try {
      setIsLoading(true);
      setError(null);
      const membersData = await api.getOrganizationMembers(currentOrganization.id);
      setMembers(membersData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load team members');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRoleChange = async (membershipId: string, newRole: MembershipRole) => {
    try {
      await api.updateMemberRole(membershipId, newRole);
      await loadMembers();
      setToast({ message: 'Member role updated successfully', type: 'success' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update member role');
      setToast({ message: 'Failed to update member role', type: 'error' });
    }
  };

  const handleRemoveMemberClick = (membershipId: string) => {
    setMemberToRemove(membershipId);
    setShowConfirmDialog(true);
  };

  const handleRemoveMember = async () => {
    if (!memberToRemove) return;

    try {
      await api.removeMember(memberToRemove);
      await loadMembers();
      setToast({ message: 'Team member removed successfully', type: 'success' });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove team member');
      setToast({ message: 'Failed to remove team member', type: 'error' });
    } finally {
      setMemberToRemove(null);
      setShowConfirmDialog(false);
    }
  };

  useEffect(() => {
    loadMembers();
  }, [currentOrganization]);

  if (!currentOrganization) {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Team Members</h1>
        </div>
        <Card className="p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">No Organization Selected</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Please select an organization to view and manage team members.
          </p>
        </Card>
      </div>
    );
  }

  if (userRole !== 'admin') {
    return (
      <div className="space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Team Members</h1>
        </div>
        <Card className="p-8 text-center">
          <div className="mx-auto w-16 h-16 bg-yellow-100 dark:bg-yellow-900/30 rounded-full flex items-center justify-center mb-4">
            <svg className="w-8 h-8 text-yellow-600 dark:text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Access Restricted</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            You don't have permission to manage team members. Please contact an administrator.
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
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Team Members</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage team members for {currentOrganization.name}
          </p>
        </div>
        <button
          onClick={() => navigate('/invitations')}
          className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white px-6 py-2.5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 font-medium flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <span>Invite Members</span>
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
            <span>Team Members</span>
            <span className="ml-2 px-2.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs font-medium rounded-full">
              {members.length}
            </span>
          </h3>
        </div>

        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {members.map((member) => (
            <div key={member.id} className="px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center space-x-4">
                {member.user_avatar ? (
                  <img
                    src={member.user_avatar}
                    alt={member.user_name}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-semibold shadow-md">
                    {member.user_name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{member.user_name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{member.user_email}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    Joined {new Date(member.joined_at).toLocaleDateString()}
                    {member.last_accessed && (
                      <> • Last active {new Date(member.last_accessed).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3 ml-14 sm:ml-0">
                <select
                  value={member.role}
                  onChange={(e) => handleRoleChange(member.id, e.target.value as MembershipRole)}
                  className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="viewer">👁️ Viewer</option>
                  <option value="editor">✏️ Editor</option>
                  <option value="admin">👑 Admin</option>
                </select>

                <button
                  onClick={() => handleRemoveMemberClick(member.id)}
                  className="px-3 py-1.5 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg text-sm transition-colors"
                  title="Remove member"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}

          {members.length === 0 && (
            <div className="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
              <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
              <p className="text-lg font-medium text-gray-900 dark:text-white mb-2">No team members yet</p>
              <p className="text-gray-600 dark:text-gray-400 mb-6">
                Invite team members to collaborate in your organization.
              </p>
              <button
                onClick={() => navigate('/invitations')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Send Invitations
              </button>
            </div>
          )}
        </div>
      </Card>

      {/* Confirm Remove Dialog */}
      <ConfirmDialog
        isOpen={showConfirmDialog}
        onClose={() => {
          setShowConfirmDialog(false);
          setMemberToRemove(null);
        }}
        onConfirm={handleRemoveMember}
        title="Remove Team Member"
        message="Are you sure you want to remove this team member? They will lose access to this organization and all its data."
        confirmText="Remove"
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

export default TeamMembers;