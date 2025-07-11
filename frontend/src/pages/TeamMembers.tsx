import React, { useState, useEffect } from 'react';
import { useOrganization } from '../hooks/useOrganization';
import { api } from '../utils/api';
import Card from '../components/ui/Card';
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update member role');
    }
  };

  const handleRemoveMember = async (membershipId: string) => {
    if (!confirm('Are you sure you want to remove this team member?')) return;

    try {
      await api.removeMember(membershipId);
      await loadMembers();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove team member');
    }
  };

  useEffect(() => {
    loadMembers();
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
          You don't have permission to manage team members
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
          <h1 className="text-2xl font-bold text-gray-900">Team Members</h1>
          <p className="text-gray-600 mt-1">
            Manage team members for {currentOrganization.name}
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      <Card className="overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Team Members ({members.length})
          </h3>
        </div>

        <div className="divide-y divide-gray-200">
          {members.map((member) => (
            <div key={member.id} className="px-6 py-4 flex items-center justify-between">
              <div className="flex items-center space-x-4">
                {member.user_avatar ? (
                  <img
                    src={member.user_avatar}
                    alt={member.user_name}
                    className="w-10 h-10 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-10 h-10 rounded-full bg-gray-500 flex items-center justify-center text-white font-semibold">
                    {member.user_name.charAt(0).toUpperCase()}
                  </div>
                )}
                <div>
                  <p className="text-sm font-medium text-gray-900">{member.user_name}</p>
                  <p className="text-sm text-gray-500">{member.user_email}</p>
                  <p className="text-xs text-gray-400">
                    Joined {new Date(member.joined_at).toLocaleDateString()}
                    {member.last_accessed && (
                      <> • Last active {new Date(member.last_accessed).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <select
                  value={member.role}
                  onChange={(e) => handleRoleChange(member.id, e.target.value as MembershipRole)}
                  className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="viewer">👁️ Viewer</option>
                  <option value="editor">✏️ Editor</option>
                  <option value="admin">👑 Admin</option>
                </select>

                <button
                  onClick={() => handleRemoveMember(member.id)}
                  className="px-3 py-1 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-md text-sm transition-colors"
                  title="Remove member"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}

          {members.length === 0 && (
            <div className="px-6 py-12 text-center text-gray-500">
              No team members found
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default TeamMembers; 
