import React from 'react';
import { RouteObject } from 'react-router-dom';
import { Dashboard, Contacts, Deals, Activities } from '../pages';
import NotFound from '../pages/NotFound';

// Lazy load organization management pages
const Organizations = React.lazy(() => import('../pages/Organizations'));
const OrganizationSettings = React.lazy(() => import('../pages/OrganizationSettings'));
const TeamMembers = React.lazy(() => import('../pages/TeamMembers'));
const Invitations = React.lazy(() => import('../pages/Invitations'));

// Route configuration interface
export interface RouteConfig {
  path: string;
  label: string;
  icon: string;
  description?: string;
  requiresRole?: 'viewer' | 'editor' | 'admin';
}

// Navigation routes for the main menu
export const navigationRoutes: RouteConfig[] = [
  {
    path: '/',
    label: 'Dashboard',
    icon: '📊',
    description: 'Overview and statistics'
  },
  {
    path: '/contacts',
    label: 'Contacts',
    icon: '👥',
    description: 'Manage customer contacts'
  },
  {
    path: '/deals',
    label: 'Deals',
    icon: '💰',
    description: 'Track sales opportunities'
  },
  {
    path: '/activities',
    label: 'Activities',
    icon: '📋',
    description: 'Manage tasks and activities'
  },
];

// Organization management routes (admin only)
export const organizationRoutes: RouteConfig[] = [
  {
    path: '/organizations',
    label: 'Organizations',
    icon: '🏢',
    description: 'Manage organizations',
    requiresRole: 'admin'
  },
  {
    path: '/team',
    label: 'Team',
    icon: '👥',
    description: 'Manage team members',
    requiresRole: 'admin'
  },
  {
    path: '/invitations',
    label: 'Invitations',
    icon: '📧',
    description: 'Manage invitations',
    requiresRole: 'admin'
  },
  {
    path: '/settings',
    label: 'Settings',
    icon: '⚙️',
    description: 'Organization settings',
    requiresRole: 'admin'
  },
];

// Route definitions for React Router
export const createAppRoutes = (
  dashboardProps: any,
  contactsProps: any,
  dealsProps: any,
  activitiesProps: any
): RouteObject[] => [
  {
    index: true,
    element: <Dashboard {...dashboardProps} />
  },
  {
    path: 'contacts',
    children: [
      {
        index: true,
        element: <Contacts {...contactsProps} />
      },
      {
        path: ':id',
        element: <Contacts {...contactsProps} /> // Future: ContactDetails component
      }
    ]
  },
  {
    path: 'deals',
    children: [
      {
        index: true,
        element: <Deals {...dealsProps} />
      },
      {
        path: ':id',
        element: <Deals {...dealsProps} /> // Future: DealDetails component
      },
      {
        path: 'by-stage/:stage',
        element: <Deals {...dealsProps} /> // Filtered deals by stage
      }
    ]
  },
  {
    path: 'activities',
    children: [
      {
        index: true,
        element: <Activities {...activitiesProps} />
      },
      {
        path: ':id',
        element: <Activities {...activitiesProps} /> // Future: ActivityDetails component
      },
      {
        path: 'by-contact/:contactId',
        element: <Activities {...activitiesProps} /> // Activities filtered by contact
      },
      {
        path: 'by-deal/:dealId',
        element: <Activities {...activitiesProps} /> // Activities filtered by deal
      }
    ]
  },
  // Organization management routes
  {
    path: 'organizations',
    children: [
      {
        index: true,
        element: (
          <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
            <Organizations />
          </React.Suspense>
        )
      },
      {
        path: ':id/settings',
        element: (
          <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
            <OrganizationSettings />
          </React.Suspense>
        )
      }
    ]
  },
  {
    path: 'team',
    children: [
      {
        index: true,
        element: (
          <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
            <TeamMembers />
          </React.Suspense>
        )
      }
    ]
  },
  {
    path: 'invitations',
    children: [
      {
        index: true,
        element: (
          <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
            <Invitations />
          </React.Suspense>
        )
      }
    ]
  },
  {
    path: 'settings',
    children: [
      {
        index: true,
        element: (
          <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
            <OrganizationSettings />
          </React.Suspense>
        )
      }
    ]
  },
  // Future routes can be added here
  {
    path: 'reports',
    children: [
      {
        index: true,
        element: <div className="p-6 text-center text-gray-500">Reports coming soon...</div>
      }
    ]
  },
  // Catch-all route for 404
  {
    path: '*',
    element: <NotFound />
  }
];

export default createAppRoutes; 
