import React from 'react';
import { RouteObject } from 'react-router-dom';
import { Dashboard, Contacts, Deals, Activities } from '../pages';
import NotFound from '../pages/NotFound';

// Route configuration interface
export interface RouteConfig {
  path: string;
  label: string;
  icon: string;
  description?: string;
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
  {
    path: 'settings',
    children: [
      {
        index: true,
        element: <div className="p-6 text-center text-gray-500">Settings coming soon...</div>
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