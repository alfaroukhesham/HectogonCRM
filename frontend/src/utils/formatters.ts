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
    Lead: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200',
    Qualified: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200',
    Proposal: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
    Negotiation: 'bg-orange-100 dark:bg-orange-900 text-orange-800 dark:text-orange-200',
    'Closed Won': 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
    'Closed Lost': 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
  };
  return colors[stage] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
};

/**
 * Gets Tailwind CSS classes for activity priority badges
 */
export const getPriorityColor = (priority: ActivityPriority): string => {
  const colors: Record<ActivityPriority, string> = {
    Low: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200',
    Medium: 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200',
    High: 'bg-red-100 dark:bg-red-900 text-red-800 dark:text-red-200',
  };
  return colors[priority] || 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200';
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