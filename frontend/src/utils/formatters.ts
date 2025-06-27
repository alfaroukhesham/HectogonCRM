import { DealStage, ActivityPriority } from '@/types';

/**
 * Formats a number as currency in USD
 */
export const formatCurrency = (amount: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
};

/**
 * Formats a date string to a localized date
 */
export const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleDateString();
};

/**
 * Formats a date string to a localized date and time
 */
export const formatDateTime = (dateString: string | undefined): string => {
  if (!dateString) return '';
  return new Date(dateString).toLocaleString();
};

/**
 * Gets Tailwind CSS classes for deal stage badges
 */
export const getStageColor = (stage: DealStage): string => {
  const colors: Record<DealStage, string> = {
    Lead: 'bg-gray-100 text-gray-800',
    Qualified: 'bg-blue-100 text-blue-800',
    Proposal: 'bg-yellow-100 text-yellow-800',
    Negotiation: 'bg-orange-100 text-orange-800',
    'Closed Won': 'bg-green-100 text-green-800',
    'Closed Lost': 'bg-red-100 text-red-800',
  };
  return colors[stage] || 'bg-gray-100 text-gray-800';
};

/**
 * Gets Tailwind CSS classes for activity priority badges
 */
export const getPriorityColor = (priority: ActivityPriority): string => {
  const colors: Record<ActivityPriority, string> = {
    Low: 'bg-green-100 text-green-800',
    Medium: 'bg-yellow-100 text-yellow-800',
    High: 'bg-red-100 text-red-800',
  };
  return colors[priority] || 'bg-gray-100 text-gray-800';
};

/**
 * Gets a contact's full name from first and last name
 */
export const getFullName = (firstName: string, lastName: string): string => {
  return `${firstName} ${lastName}`.trim();
};

/**
 * Gets initials from first and last name
 */
export const getInitials = (firstName: string, lastName: string): string => {
  const firstInitial = firstName.charAt(0).toUpperCase();
  const lastInitial = lastName.charAt(0).toUpperCase();
  return `${firstInitial}${lastInitial}`;
}; 