import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DashboardStats, Activity, Contact, Deal } from '@/types';
import { formatCurrency } from '@/utils/formatters';
import { StatCard, Chart, RecentActivity, QuickActions, Card } from '@/components/ui';
import { apiService } from '@/utils/api';

interface DashboardProps {
  dashboardStats: DashboardStats;
  isLoading: boolean;
}

const Dashboard: React.FC<DashboardProps> = ({ dashboardStats, isLoading }) => {
  const navigate = useNavigate();
  const [mounted, setMounted] = useState(false);
  const [recentActivities, setRecentActivities] = useState<Activity[]>([]);
  const [recentContacts, setRecentContacts] = useState<Contact[]>([]);
  const [recentDeals, setRecentDeals] = useState<Deal[]>([]);
  const [loadingActivities, setLoadingActivities] = useState(true);

  useEffect(() => {
    setMounted(true);
    loadRecentData();
  }, []);

  const loadRecentData = async () => {
    try {
      setLoadingActivities(true);
      const [activities, contacts, deals] = await Promise.all([
        apiService.getActivities(),
        apiService.getContacts(),
        apiService.getDeals()
      ]);
      
      // Get the 5 most recent activities
      setRecentActivities(activities.slice(0, 5));
      
      // Get the 3 most recent contacts
      setRecentContacts(contacts.slice(0, 3));
      
      // Get the 3 most recent deals
      setRecentDeals(deals.slice(0, 3));
    } catch (error) {
      console.error('Error loading recent data:', error);
    } finally {
      setLoadingActivities(false);
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

  if (isLoading) {
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

  // Prepare chart data from real backend data
  const stageData = Object.entries(dashboardStats.deals_by_stage || {}).map(([stage, count], index) => ({
    label: stage,
    value: count,
    color: [
      '#3B82F6', // Blue
      '#10B981', // Green  
      '#F59E0B', // Yellow
      '#EF4444', // Red
      '#8B5CF6', // Purple
      '#6B7280'  // Gray
    ][index % 6]
  }));

  // Calculate trend data based on real data (mock implementation)
  const generateTrendData = (baseValue: number) => {
    return Array.from({ length: 12 }, (_, i) => {
      const variation = Math.sin(i * 0.5) * 0.3 + Math.random() * 0.2;
      return Math.max(1, Math.round(baseValue * (1 + variation)));
    });
  };

  // Calculate win rate
  const wonDeals = dashboardStats.deals_by_stage?.['Closed Won'] || 0;
  const totalDeals = dashboardStats.total_deals || 1;
  const winRate = Math.round((wonDeals / totalDeals) * 100);

  // Calculate average deal value
  const avgDealValue = wonDeals > 0 ? dashboardStats.total_revenue / wonDeals : 0;

  // Calculate hot leads (Proposal + Negotiation)
  const hotLeads = (dashboardStats.deals_by_stage?.['Proposal'] || 0) + 
                   (dashboardStats.deals_by_stage?.['Negotiation'] || 0);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className={`mb-8 transition-all duration-700 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Welcome back! 👋
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                Here's what's happening with your business today.
              </p>
            </div>
            <div className="hidden md:flex items-center space-x-3">
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Last updated: {new Date().toLocaleTimeString()}
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8 transition-all duration-700 delay-100 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          <StatCard
            title="Total Contacts"
            value={dashboardStats.total_contacts.toLocaleString()}
            change={{ value: 12, type: 'increase' }}
            icon="👥"
            color="blue"
            trend={generateTrendData(dashboardStats.total_contacts)}
          />
          <StatCard
            title="Active Deals"
            value={dashboardStats.total_deals.toLocaleString()}
            change={{ value: 8, type: 'increase' }}
            icon="💼"
            color="green"
            trend={generateTrendData(dashboardStats.total_deals)}
          />
          <StatCard
            title="Total Revenue"
            value={formatCurrency(dashboardStats.total_revenue)}
            change={{ value: 23, type: 'increase' }}
            icon="💰"
            color="purple"
            trend={generateTrendData(dashboardStats.total_revenue / 1000)}
          />
          <StatCard
            title="Pipeline Value"
            value={formatCurrency(dashboardStats.pipeline_value)}
            change={{ value: 5, type: 'increase' }}
            icon="📈"
            color="orange"
            trend={generateTrendData(dashboardStats.pipeline_value / 1000)}
          />
        </div>

        {/* Charts and Activity Grid */}
        <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8 transition-all duration-700 delay-200 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          {/* Deals by Stage Chart */}
          <div className="lg:col-span-2">
            <Chart
              title="Deals by Stage"
              data={stageData}
              type="bar"
            />
          </div>
          
          {/* Recent Activity */}
          <div>
            <RecentActivity 
              activities={loadingActivities ? [] : allRecentItems} 
            />
          </div>
        </div>

        {/* Bottom Grid */}
        <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 transition-all duration-700 delay-300 ${mounted ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}>
          {/* Quick Actions */}
          <div>
            <QuickActions actions={quickActions} />
          </div>
          
          {/* Performance Overview */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6">
                Performance Overview
              </h3>
              
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center p-4 rounded-xl bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-500/10 dark:to-blue-600/10">
                  <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                    {wonDeals}
                  </div>
                  <div className="text-sm text-blue-600/80 dark:text-blue-400/80 mt-1">
                    Won Deals
                  </div>
                </div>
                
                <div className="text-center p-4 rounded-xl bg-gradient-to-br from-green-50 to-green-100 dark:from-green-500/10 dark:to-green-600/10">
                  <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                    {winRate}%
                  </div>
                  <div className="text-sm text-green-600/80 dark:text-green-400/80 mt-1">
                    Win Rate
                  </div>
                </div>
                
                <div className="text-center p-4 rounded-xl bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-500/10 dark:to-purple-600/10">
                  <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                    {formatCurrency(avgDealValue)}
                  </div>
                  <div className="text-sm text-purple-600/80 dark:text-purple-400/80 mt-1">
                    Avg Deal
                  </div>
                </div>
                
                <div className="text-center p-4 rounded-xl bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-500/10 dark:to-orange-600/10">
                  <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                    {hotLeads}
                  </div>
                  <div className="text-sm text-orange-600/80 dark:text-orange-400/80 mt-1">
                    Hot Leads
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;