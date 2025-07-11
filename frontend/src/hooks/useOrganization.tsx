import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../utils/api';
import { Organization, OrganizationMembership, MembershipRole, OrganizationCreateRequest } from '../types';

interface OrganizationContextType {
  currentOrganization: Organization | null;
  organizations: OrganizationMembership[];
  userRole: MembershipRole | null;
  isLoading: boolean;
  error: string | null;
  switchOrganization: (organizationId: string) => Promise<void>;
  refreshOrganizations: () => Promise<void>;
  createOrganization: (data: OrganizationCreateRequest) => Promise<void>;
  retryLoading: () => void;
}

const OrganizationContext = createContext<OrganizationContextType | undefined>(undefined);

interface OrganizationProviderProps {
  children: ReactNode;
}

export const OrganizationProvider: React.FC<OrganizationProviderProps> = ({ children }) => {
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([]);
  const [userRole, setUserRole] = useState<MembershipRole | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOrganizations = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('Loading organizations...');
      const orgs = await api.getOrganizations();
      console.log('Organizations loaded:', orgs);
      
      setOrganizations(orgs);
      
      // If we have a current organization ID, validate it against available memberships
      const currentOrgId = api.getCurrentOrganization();
      console.log('Current stored org ID:', currentOrgId);
      console.log('Available organizations:', orgs.map(org => ({ id: org.organization_id, name: org.organization_name })));
      
      let targetOrgId = null;
      
      if (currentOrgId && orgs.length > 0) {
        const currentMembership = orgs.find(org => org.organization_id === currentOrgId);
        if (currentMembership) {
          console.log('Found matching membership for stored org ID');
          targetOrgId = currentOrgId;
        } else {
          console.warn('Stored organization ID not found in user memberships, clearing it');
          api.setCurrentOrganization(null); // Clear invalid stored org ID
        }
      }
      
      // If no valid current org, use first available
      if (!targetOrgId && orgs.length > 0) {
        targetOrgId = orgs[0].organization_id;
        console.log('Using first available organization:', targetOrgId);
      }
      
      if (targetOrgId) {
        const membership = orgs.find(org => org.organization_id === targetOrgId);
        if (membership) {
          try {
            console.log('Loading organization details for:', targetOrgId);
            const orgDetails = await api.getOrganization(targetOrgId);
            setCurrentOrganization(orgDetails);
            setUserRole(membership.role);
            
            // Update API client's current organization
            api.setCurrentOrganization(targetOrgId);
            console.log('Successfully set organization context');
          } catch (err) {
            console.error('Failed to load organization details:', err);
            setError(`Failed to load organization details: ${err instanceof Error ? err.message : 'Unknown error'}`);
          }
        } else {
          console.error('Membership not found for target organization ID:', targetOrgId);
          setError('Organization membership not found');
        }
      } else {
        // No organizations found - this might be a new user
        console.warn('No organizations found for user');
        setError('No organizations found. You may need to create an organization or be invited to one.');
      }
    } catch (err) {
      console.error('Error loading organizations:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load organizations';
      setError(errorMessage);
      
      // If it's a 403 error, it might be a permission issue
      if (err instanceof Error && err.message.includes('403')) {
        setError('Access denied. You may need to be invited to an organization or your session may have expired.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const switchOrganization = async (organizationId: string) => {
    try {
      setError(null);
      
      const membership = organizations.find(org => org.organization_id === organizationId);
      if (!membership) {
        throw new Error('Organization not found in your memberships');
      }
      
      console.log('Switching to organization:', organizationId);
      const orgDetails = await api.getOrganization(organizationId);
      setCurrentOrganization(orgDetails);
      setUserRole(membership.role);
      
      // Update API client's current organization
      api.setCurrentOrganization(organizationId);
      console.log('Organization switched successfully');
    } catch (err) {
      console.error('Error switching organization:', err);
      setError(err instanceof Error ? err.message : 'Failed to switch organization');
    }
  };

  const refreshOrganizations = async () => {
    await loadOrganizations();
  };

  const createOrganization = async (data: OrganizationCreateRequest) => {
    try {
      setError(null);
      const newOrg = await api.createOrganization(data);
      await refreshOrganizations();
      await switchOrganization(newOrg.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create organization');
      throw err;
    }
  };

  const retryLoading = () => {
    loadOrganizations();
  };

  useEffect(() => {
    // Add a timeout to prevent infinite loading
    const loadingTimeout = setTimeout(() => {
      if (isLoading) {
        console.error('Organization loading timed out');
        setError('Loading organizations timed out. Please try again.');
        setIsLoading(false);
      }
    }, 30000); // 30 second timeout

    loadOrganizations();

    return () => {
      clearTimeout(loadingTimeout);
    };
  }, []);

  const value: OrganizationContextType = {
    currentOrganization,
    organizations,
    userRole,
    isLoading,
    error,
    switchOrganization,
    refreshOrganizations,
    createOrganization,
    retryLoading,
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
};

export const useOrganization = (): OrganizationContextType => {
  const context = useContext(OrganizationContext);
  if (context === undefined) {
    throw new Error('useOrganization must be used within an OrganizationProvider');
  }
  return context;
}; 
