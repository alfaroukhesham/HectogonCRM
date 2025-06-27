import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Contact, Deal, Activity, DashboardStats } from './types';
import { apiService } from './utils/api';
import { MainLayout, ErrorBoundary } from './components';
import { Dashboard, Contacts, Deals, Activities } from './pages';
import { useTheme } from './hooks/useTheme';
import NotFound from './pages/NotFound';
import './App.css';

const App: React.FC = () => {
  // Initialize theme
  useTheme();

  const [contacts, setContacts] = useState<Contact[]>([]);
  const [deals, setDeals] = useState<Deal[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
    total_contacts: 0,
    total_deals: 0,
    total_revenue: 0,
    pipeline_value: 0,
    deals_by_stage: {
      'Lead': 0,
      'Qualified': 0,
      'Proposal': 0,
      'Negotiation': 0,
      'Closed Won': 0,
      'Closed Lost': 0,
    }
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load all data on component mount
  useEffect(() => {
    loadAllData();
  }, []);

  const loadContacts = async (): Promise<void> => {
    try {
      const contactsData = await apiService.getContacts();
      setContacts(Array.isArray(contactsData) ? contactsData : []);
    } catch (error) {
      console.error('Error loading contacts:', error);
      setContacts([]);
    }
  };

  const loadDeals = async (): Promise<void> => {
    try {
      const dealsData = await apiService.getDeals();
      setDeals(Array.isArray(dealsData) ? dealsData : []);
    } catch (error) {
      console.error('Error loading deals:', error);
      setDeals([]);
    }
  };

  const loadActivities = async (): Promise<void> => {
    try {
      const activitiesData = await apiService.getActivities();
      setActivities(Array.isArray(activitiesData) ? activitiesData : []);
    } catch (error) {
      console.error('Error loading activities:', error);
      setActivities([]);
    }
  };

  const loadDashboardStats = async (): Promise<void> => {
    try {
      const stats = await apiService.getDashboardStats();
      setDashboardStats(stats);
    } catch (error) {
      console.error('Error loading dashboard stats:', error);
    }
  };

  const loadAllData = async (): Promise<void> => {
    setIsLoading(true);
    setError(null);
    
    try {
      await Promise.all([
        loadContacts(),
        loadDeals(),
        loadActivities(),
        loadDashboardStats()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
      setError('Failed to load application data. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleContactSave = async (): Promise<void> => {
    await Promise.all([loadContacts(), loadDashboardStats()]);
  };

  const handleDealSave = async (): Promise<void> => {
    await Promise.all([loadDeals(), loadDashboardStats()]);
  };

  const handleActivitySave = async (): Promise<void> => {
    await loadActivities();
  };

  const deleteContact = async (id: string): Promise<void> => {
    if (window.confirm('Are you sure you want to delete this contact?')) {
      try {
        await apiService.deleteContact(id);
        await Promise.all([loadContacts(), loadDashboardStats()]);
      } catch (error) {
        console.error('Error deleting contact:', error);
        setError('Failed to delete contact. Please try again.');
      }
    }
  };

  const deleteDeal = async (id: string): Promise<void> => {
    if (window.confirm('Are you sure you want to delete this deal?')) {
      try {
        await apiService.deleteDeal(id);
        await Promise.all([loadDeals(), loadDashboardStats()]);
      } catch (error) {
        console.error('Error deleting deal:', error);
        setError('Failed to delete deal. Please try again.');
      }
    }
  };

  const deleteActivity = async (id: string): Promise<void> => {
    if (window.confirm('Are you sure you want to delete this activity?')) {
      try {
        await apiService.deleteActivity(id);
        await loadActivities();
      } catch (error) {
        console.error('Error deleting activity:', error);
        setError('Failed to delete activity. Please try again.');
      }
    }
  };

  // Global error display
  const ErrorDisplay: React.FC = () => {
    if (!error) return null;
    
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400">
        <div className="flex items-center justify-between">
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-red-700 hover:text-red-900 ml-4 dark:text-red-400 dark:hover:text-red-300"
          >
            ✕
          </button>
        </div>
      </div>
    );
  };

  return (
    <ErrorBoundary>
      <Router>
        <MainLayout>
          <ErrorDisplay />
          <Routes>
            <Route 
              index 
              element={
                <Dashboard
                  dashboardStats={dashboardStats}
                  isLoading={isLoading}
                />
              } 
            />
            <Route path="contacts">
              <Route 
                index
                element={
                  <Contacts
                    contacts={contacts}
                    onContactSave={handleContactSave}
                    onContactDelete={deleteContact}
                    isLoading={isLoading}
                  />
                } 
              />
              <Route 
                path=":id"
                element={
                  <Contacts
                    contacts={contacts}
                    onContactSave={handleContactSave}
                    onContactDelete={deleteContact}
                    isLoading={isLoading}
                  />
                } 
              />
            </Route>
            <Route path="deals">
              <Route 
                index
                element={
                  <Deals
                    deals={deals}
                    contacts={contacts}
                    onDealSave={handleDealSave}
                    onDealDelete={deleteDeal}
                    isLoading={isLoading}
                  />
                } 
              />
              <Route 
                path=":id"
                element={
                  <Deals
                    deals={deals}
                    contacts={contacts}
                    onDealSave={handleDealSave}
                    onDealDelete={deleteDeal}
                    isLoading={isLoading}
                  />
                } 
              />
              <Route 
                path="by-stage/:stage"
                element={
                  <Deals
                    deals={deals}
                    contacts={contacts}
                    onDealSave={handleDealSave}
                    onDealDelete={deleteDeal}
                    isLoading={isLoading}
                  />
                } 
              />
            </Route>
            <Route path="activities">
              <Route 
                index
                element={
                  <Activities
                    activities={activities}
                    contacts={contacts}
                    onActivitySave={handleActivitySave}
                    onActivityDelete={deleteActivity}
                    isLoading={isLoading}
                  />
                } 
              />
              <Route 
                path=":id"
                element={
                  <Activities
                    activities={activities}
                    contacts={contacts}
                    onActivitySave={handleActivitySave}
                    onActivityDelete={deleteActivity}
                    isLoading={isLoading}
                  />
                } 
              />
              <Route 
                path="by-contact/:contactId"
                element={
                  <Activities
                    activities={activities}
                    contacts={contacts}
                    onActivitySave={handleActivitySave}
                    onActivityDelete={deleteActivity}
                    isLoading={isLoading}
                  />
                } 
              />
              <Route 
                path="by-deal/:dealId"
                element={
                  <Activities
                    activities={activities}
                    contacts={contacts}
                    onActivitySave={handleActivitySave}
                    onActivityDelete={deleteActivity}
                    isLoading={isLoading}
                  />
                } 
              />
            </Route>
            <Route path="reports">
              <Route 
                index
                element={<div className="p-6 text-center text-gray-500 dark:text-gray-400">Reports coming soon...</div>}
              />
            </Route>
            <Route path="settings">
              <Route 
                index
                element={<div className="p-6 text-center text-gray-500 dark:text-gray-400">Settings coming soon...</div>}
              />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Routes>
        </MainLayout>
      </Router>
    </ErrorBoundary>
  );
};

export default App;