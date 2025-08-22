import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Activity, Contact, Deal } from '../types';
import { formatCurrency } from '../utils/formatters';
import { StatCard, Chart, RecentActivity, QuickActions, Card } from '../components/ui';
import { api } from '../utils/api';
import { useOrganization } from '../hooks/useOrganization';

interface DashboardStats {
  total_contacts: number;
  total_deals: number;
  total_activities: number;
  won_deals: number;
  total_revenue: number;
  pipeline_value: number;
  deals_by_stage: Record<string, number>;
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const { currentOrganization, isLoading: orgLoading, error: orgError, retryLoading } = useOrganization();
  const [mounted, setMounted] = useState(false);
  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
    total_contacts: 0,
    total_deals: 0,
    total_activities: 0,
    won_deals: 0,
    total_revenue: 0,
    pipeline_value: 0,
    deals_by_stage: {}
  });
  const [recentActivities, setRecentActivities] = useState<Activity[]>([]);
  const [recentContacts, setRecentContacts] = useState<Contact[]>([]);
  const [recentDeals, setRecentDeals] = useState<Deal[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Load dashboard data when organization context is ready
  useEffect(() => {
    if (mounted && currentOrganization && !orgLoading) {
      loadDashboardData();
    }
  }, [mounted, currentOrganization, orgLoading]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const [stats, activities, contacts, deals] = await Promise.all([
        api.getDashboardStats(),
        api.getActivities(),
        api.getContacts(),
        api.getDeals()
      ]);
      
      setDashboardStats(stats);
      setRecentActivities(activities.slice(0, 5));
      setRecentContacts(contacts.slice(0, 3));
      setRecentDeals(deals.slice(0, 3));
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };

  const quickActions = [
    {
      id: '1',
      title: 'Add Contact',
      description: 'Create new contact',
      icon: '👤',
      color: 'from-blue-500 to-blue-600',
      onClick: () => navigate('/contacts')
    },
    {
      id: '2',
      title: 'New Deal',
      description: 'Track opportunity',
      icon: '💰',
      color: 'from-green-500 to-green-600',
      onClick: () => navigate('/deals')
    },
    {
      id: '3',
      title: 'Log Activity',
      description: 'Record interaction',
      icon: '📋',
      color: 'from-purple-500 to-purple-600',
      onClick: () => navigate('/activities')
    },
    {
      id: '4',
      title: 'View Reports',
      description: 'Analytics & insights',
      icon: '📊',
      color: 'from-orange-500 to-orange-600',
      onClick: () => navigate('/reports')
    }
  ];

  // Transform recent activities for the RecentActivity component
  const transformedActivities = recentActivities.map(activity => ({
    id: activity.id,
    type: 'activity' as const,
    title: activity.title,
    description: activity.description || `${activity.type} activity`,
    time: new Date(activity.created_at).toLocaleDateString(),
    user: 'You'
  }));

  // Add recent contacts and deals to activities
  const allRecentItems = [
    ...transformedActivities,
    ...recentContacts.map(contact => ({
      id: contact.id,
      type: 'contact' as const,
      title: 'New contact added',
      description: `${contact.first_name} ${contact.last_name} from ${contact.company || 'Unknown Company'}`,
      time: new Date(contact.created_at).toLocaleDateString(),
      user: 'You'
    })),
    ...recentDeals.map(deal => ({
      id: deal.id,
      type: 'deal' as const,
      title: 'Deal created',
      description: `${deal.title} - ${formatCurrency(deal.value)}`,
      time: new Date(deal.created_at).toLocaleDateString(),
      user: 'You'
    }))
  ].sort((a, b) => new Date(b.time).getTime() - new Date(a.time).getTime()).slice(0, 5);

  // Show loading while organization context is being loaded OR data is being fetched
  if (orgLoading || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          {/* Header Skeleton */}
          <div className="mb-8">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded-lg w-64 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-96 animate-pulse"></div>
          </div>
          
          {/* Stats Grid Skeleton */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white dark:bg-gray-800 rounded-xl p-6 animate-pulse">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-12 h-12 bg-gray-200 dark:bg-gray-700 rounded-xl"></div>
                  <div className="w-16 h-6 bg-gray-200 dark:bg-gray-700 rounded-full"></div>
                </div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24"></div>
                  <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                </div>
              </div>
            ))}
          </div>
          
          {/* Charts Skeleton */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-6"></div>
              <div className="space-y-4">
                {[...Array(6)].map((_, i) => (
                  <div key={i} className="space-y-2">
                    <div className="flex justify-between">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20"></div>
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-8"></div>
                    </div>
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded"></div>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl p-6 animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-32 mb-6"></div>
              <div className="w-48 h-48 bg-gray-200 dark:bg-gray-700 rounded-full mx-auto"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show error message if organization loading failed
  if (orgError) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mt-20">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">Organization Loading Failed</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-8">{orgError}</p>
            <div className="space-x-4">
              <button
                onClick={retryLoading}
                className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
              >
                Retry
              </button>
              <button
                onClick={() => navigate('/organizations')}
                className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-md transition-colors"
              >
                Manage Organizations
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Show message if no organization is selected
  if (!currentOrganization) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mt-20">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">No Organization Selected</h1>
            <p className="text-gray-600 dark:text-gray-400 mb-8">Please select an organization to view your dashboard.</p>
            <button
              onClick={() => navigate('/organizations')}
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md transition-colors"
            >
              Select Organization
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6">
        <div className="max-w-7xl mx-auto">
          <div className="bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-3 rounded-md">
            <div className="flex items-center justify-between">
              <span>{error}</span>
              <button
                onClick={loadDashboardData}
                className="text-red-700 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 ml-4"
              >
                Retry
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Prepare chart data from real backend data
  const stageData = Object.entries(dashboardStats.deals_by_stage || {}).map(([stage, count], index) => {
    const colors = [
      '#3B82F6', // Blue
      '#10B981', // Green  
      '#F59E0B', // Yellow
      '#EF4444', // Red
      '#8B5CF6', // Purple
      '#6B7280'  // Gray
    ];
    return {
      label: stage,
      value: count,
      color: colors[index % colors.length] || '#6B7280' // Fallback to gray
    };
  });

  // Calculate trend data based on real data (mock implementation)
  const generateTrendData = (baseValue: number) => {
    return Array.from({ length: 12 }, (_, i) => {
      const variation = Math.sin(i * 0.5) * 0.3 + Math.random() * 0.2;
      return Math.max(1, Math.round(baseValue * (1 + variation)));
    });
  };

  // Calculate win rate
  const wonDeals = dashboardStats.deals_by_stage?.['closed_won'] || dashboardStats.deals_by_stage?.['Closed Won'] || 0;
  const totalDeals = dashboardStats.total_deals || 1;
  const winRate = Math.round((wonDeals / totalDeals) * 100);

  // Calculate average deal value
  const avgDealValue = wonDeals > 0 ? dashboardStats.total_revenue / wonDeals : 0;

  // Calculate hot leads (Proposal + Negotiation)
  const hotLeads = (dashboardStats.deals_by_stage?.['proposal'] || dashboardStats.deals_by_stage?.['Proposal'] || 0) + 
                   (dashboardStats.deals_by_stage?.['negotiation'] || dashboardStats.deals_by_stage?.['Negotiation'] || 0);

  return (
    <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Welcome back! Here's what's happening with your business today.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Contacts"
            value={dashboardStats.total_contacts.toString()}
            change={{ value: 12, type: 'increase' }}
            trend={generateTrendData(dashboardStats.total_contacts)}
            icon="👥"
            color="blue"
          />
          <StatCard
            title="Active Deals"
            value={dashboardStats.total_deals.toString()}
            change={{ value: 8, type: 'increase' }}
            trend={generateTrendData(dashboardStats.total_deals)}
            icon="💼"
            color="green"
          />
          <StatCard
            title="Revenue"
            value={formatCurrency(dashboardStats.total_revenue)}
            change={{ value: 23, type: 'increase' }}
            trend={generateTrendData(dashboardStats.total_revenue / 1000)}
            icon="💰"
            color="purple"
          />
          <StatCard
            title="Win Rate"
            value={`${winRate}%`}
            change={{ value: 5, type: 'increase' }}
            trend={generateTrendData(winRate)}
            icon="🎯"
            color="orange"
          />
        </div>

        {/* Charts and Quick Actions */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Deal Pipeline Chart */}
          <div className="lg:col-span-2">
            <Card className="h-full">
              <div className="p-6">
                <Chart
                  title="Deal Pipeline"
                  type="bar"
                  data={stageData}
                />
              </div>
            </Card>
          </div>

          {/* Quick Actions */}
          <div>
            <QuickActions actions={quickActions} />
          </div>
        </div>

        {/* Recent Activity and Performance Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Activity */}
          <Card className="h-full">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Recent Activity</h3>
              <RecentActivity activities={allRecentItems} />
            </div>
          </Card>

          {/* Performance Metrics */}
          <Card className="h-full">
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Performance Metrics</h3>
              <div className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Pipeline Value</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatCurrency(dashboardStats.pipeline_value)}
                    </p>
                  </div>
                  <div className="text-green-500">
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M3.293 9.707a1 1 0 010-1.414l6-6a1 1 0 011.414 0l6 6a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L4.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Avg Deal Value</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatCurrency(avgDealValue)}
                    </p>
                  </div>
                  <div className="text-blue-500">
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z" />
                      <path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z" />
                    </svg>
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Hot Leads</p>
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {hotLeads}
                    </p>
                  </div>
                  <div className="text-red-500">
                    <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M12.395 2.553a1 1 0 00-1.45-.385c-.345.23-.614.558-.822.88-.214.33-.403.713-.57 1.116-.334.804-.614 1.768-.84 2.734a31.365 31.365 0 00-.613 3.58 2.64 2.64 0 01-.945-1.067c-.328-.68-.398-1.534-.398-2.654A1 1 0 005.05 6.05 6.981 6.981 0 003 11a7 7 0 1011.95-4.95c-.592-.591-.98-.985-1.348-1.467-.363-.476-.724-1.063-1.207-2.03zM12.12 15.12A3 3 0 017 13s.879.5 2.5.5c0-1 .5-4 1.25-4.5.5 1 .786 1.293 1.371 1.879A2.99 2.99 0 0113 13a2.99 2.99 0 01-.879 2.121z" clipRule="evenodd" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
    </div>
  );
};

export default Dashboard;
