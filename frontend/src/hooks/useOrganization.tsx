import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../utils/api';
import { Organization, OrganizationMembership, MembershipRole, OrganizationCreateRequest } from '../types';
import { useAuth } from './useAuth';

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
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const [currentOrganization, setCurrentOrganization] = useState<Organization | null>(null);
  const [organizations, setOrganizations] = useState<OrganizationMembership[]>([]);
  const [userRole, setUserRole] = useState<MembershipRole | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadOrganizations = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const orgs = await api.getOrganizations();
      
      setOrganizations(orgs);
      
      // If we have a current organization ID, validate it against available memberships
      const currentOrgId = api.getCurrentOrganization();
      
      let targetOrgId = null;
      
      if (currentOrgId && orgs.length > 0) {
        const currentMembership = orgs.find(org => org.organization_id === currentOrgId);
        if (currentMembership) {
          targetOrgId = currentOrgId;
        } else {
          console.warn('Stored organization ID not found in user memberships, clearing it');
          api.setCurrentOrganization(null); // Clear invalid stored org ID
        }
      }
      
      // If no valid current org, use first available
      if (!targetOrgId && orgs.length > 0) {
        const firstOrg = orgs[0];
        if (firstOrg) {
          targetOrgId = firstOrg.organization_id;
        }
      }
      
      if (targetOrgId) {
        const membership = orgs.find(org => org.organization_id === targetOrgId);
        if (membership) {
          try {
            const orgDetails = await api.getOrganization(targetOrgId);
            setCurrentOrganization(orgDetails);
            setUserRole(membership.role);
            
            // Update API client's current organization
            api.setCurrentOrganization(targetOrgId);
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
      
      const orgDetails = await api.getOrganization(organizationId);
      setCurrentOrganization(orgDetails);
      setUserRole(membership.role);
      
      // Update API client's current organization
      api.setCurrentOrganization(organizationId);
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
    const initializeOrganizations = async () => {
      // If auth is still loading, wait
      if (authLoading) {
        setIsLoading(true);
        return;
      }
      
      // Only load organizations if user is authenticated
      if (!isAuthenticated) {
        // If not authenticated, set loading to false and clear any previous state
        setIsLoading(false);
        setCurrentOrganization(null);
        setOrganizations([]);
        setUserRole(null);
        setError(null);
        return;
      }


      try {
        await loadOrganizations();
      } catch (error) {
        console.error('OrganizationProvider: Critical error during initialization:', error);
        // Set a fallback error state if loadOrganizations didn't handle it
        setError(error instanceof Error ? error.message : 'Failed to initialize organizations');
        setIsLoading(false);
      }
    };

    initializeOrganizations();
  }, [isAuthenticated, authLoading]);

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
