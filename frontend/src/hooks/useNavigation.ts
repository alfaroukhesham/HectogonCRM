import { useNavigate, useLocation } from 'react-router-dom';
import { useMemo } from 'react';
import { navigationRoutes, RouteConfig } from '../router/routes';

export interface NavigationItem {
  to: string;
  label: string;
  icon: string;
  description?: string;
}

export interface UseNavigationReturn {
  navigationItems: NavigationItem[];
  currentPath: string;
  navigate: (path: string) => void;
  isCurrentPath: (path: string) => boolean;
  goToDashboard: () => void;
  goToContacts: () => void;
  goToDeals: () => void;
  goToActivities: () => void;
}

export const useNavigation = (): UseNavigationReturn => {
  const navigate = useNavigate();
  const location = useLocation();

  const navigationItems: NavigationItem[] = useMemo(() => 
    navigationRoutes.map(route => ({
      to: route.path,
      label: route.label,
      icon: route.icon,
      ...(route.description && { description: route.description })
    })), []);

  const currentPath = location.pathname;

  const isCurrentPath = (path: string): boolean => {
    if (path === '/') {
      return currentPath === '/';
    }
    return currentPath.startsWith(path);
  };

  const navigateTo = (path: string): void => {
    navigate(path);
  };

  // Convenience navigation methods
  const goToDashboard = (): void => { navigate('/'); };
  const goToContacts = (): void => { navigate('/contacts'); };
  const goToDeals = (): void => { navigate('/deals'); };
  const goToActivities = (): void => { navigate('/activities'); };

  return {
    navigationItems,
    currentPath,
    navigate: navigateTo,
    isCurrentPath,
    goToDashboard,
    goToContacts,
    goToDeals,
    goToActivities,
  };
}; 