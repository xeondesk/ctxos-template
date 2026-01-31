import React from 'react';
import { useQuery } from 'react-query';
import {
  ChartBarIcon,
  ServerIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { apiClient } from 'api';

// Components
import StatCard from 'components/StatCard';
import RiskChart from 'components/RiskChart';
import RecentActivity from 'components/RecentActivity';
import TopRisks from 'components/TopRisks';

const DashboardPage: React.FC = () => {
  // Fetch dashboard data
  const { data: healthData, isLoading: healthLoading } = useQuery(
    'health-status',
    () => apiClient.getHealth(),
    { refetchInterval: 30000 } // Refetch every 30 seconds
  );

  const { data: scoringStatus, isLoading: scoringLoading } = useQuery(
    'scoring-status',
    () => apiClient.getScoringStatus(),
    { refetchInterval: 60000 }
  );

  const { data: agentHealth, isLoading: agentLoading } = useQuery(
    'agent-health',
    () => apiClient.getAgentHealth(),
    { refetchInterval: 60000 }
  );

  const { data: configHealth, isLoading: configLoading } = useQuery(
    'config-health',
    () => apiClient.getConfigHealth(),
    { refetchInterval: 60000 }
  );

  // Mock data for demonstration
  const mockStats = {
    totalEntities: 1247,
    criticalRisks: 23,
    activeAgents: 4,
    recentScans: 156,
  };

  const mockRiskData = [
    { name: 'Critical', value: 23, color: '#dc2626' },
    { name: 'High', value: 67, color: '#f59e0b' },
    { name: 'Medium', value: 234, color: '#eab308' },
    { name: 'Low', value: 456, color: '#3b82f6' },
    { name: 'Info', value: 467, color: '#6b7280' },
  ];

  const mockRecentActivity = [
    {
      id: '1',
      type: 'scan',
      message: 'Completed security scan on web-server-01',
      timestamp: '2024-01-15T10:30:00Z',
      severity: 'success',
    },
    {
      id: '2',
      type: 'alert',
      message: 'Critical vulnerability detected on db-server-02',
      timestamp: '2024-01-15T10:15:00Z',
      severity: 'error',
    },
    {
      id: '3',
      type: 'agent',
      message: 'Gap detector analysis completed for subnet-192.168.1',
      timestamp: '2024-01-15T09:45:00Z',
      severity: 'info',
    },
    {
      id: '4',
      type: 'config',
      message: 'Updated scoring rule: critical-vulnerability-multiplier',
      timestamp: '2024-01-15T09:30:00Z',
      severity: 'warning',
    },
  ];

  const mockTopRisks = [
    {
      id: '1',
      entityName: 'web-server-01',
      entityType: 'host',
      score: 92,
      severity: 'critical',
      topIssues: ['CVE-2023-1234', 'Open port 8080', 'SSL expiring'],
    },
    {
      id: '2',
      entityName: 'db-server-02',
      entityType: 'host',
      score: 88,
      severity: 'high',
      topIssues: ['MySQL vulnerability', 'Weak authentication'],
    },
    {
      id: '3',
      entityName: 'api.example.com',
      entityType: 'domain',
      score: 85,
      severity: 'high',
      topIssues: ['Subdomain takeover', 'DNS misconfiguration'],
    },
    {
      id: '4',
      entityName: 'admin-user',
      entityType: 'user',
      score: 78,
      severity: 'medium',
      topIssues: ['Weak password', 'MFA disabled'],
    },
    {
      id: '5',
      entityName: 'vpn-gateway',
      entityType: 'host',
      score: 75,
      severity: 'medium',
      topIssues: ['Outdated software', 'Open management port'],
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Overview of your security posture and system status
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Entities"
          value={mockStats.totalEntities}
          icon={<ServerIcon className="h-6 w-6" />}
          trend={{ value: 12, isPositive: true }}
          loading={false}
        />
        <StatCard
          title="Critical Risks"
          value={mockStats.criticalRisks}
          icon={<ExclamationTriangleIcon className="h-6 w-6" />}
          trend={{ value: 3, isPositive: false }}
          loading={false}
        />
        <StatCard
          title="Active Agents"
          value={mockStats.activeAgents}
          icon={<ShieldCheckIcon className="h-6 w-6" />}
          loading={agentLoading}
        />
        <StatCard
          title="Recent Scans"
          value={mockStats.recentScans}
          icon={<ChartBarIcon className="h-6 w-6" />}
          trend={{ value: 8, isPositive: true }}
          loading={false}
        />
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Risk Distribution Chart */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              Risk Distribution
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Breakdown of risk levels across all entities
            </p>
          </div>
          <div className="card-body">
            <RiskChart data={mockRiskData} />
          </div>
        </div>

        {/* System Health */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              System Health
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Status of core services and components
            </p>
          </div>
          <div className="card-body">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm font-medium text-gray-900">
                    API Server
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {healthLoading ? 'Loading...' : 'Healthy'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm font-medium text-gray-900">
                    Scoring Engine
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {scoringLoading ? 'Loading...' : 'Operational'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm font-medium text-gray-900">
                    AI Agents
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {agentLoading ? 'Loading...' : 'All Active'}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="h-2 w-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm font-medium text-gray-900">
                    Configuration
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {configLoading ? 'Loading...' : 'Synced'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Activity and Top Risks */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Recent Activity */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              Recent Activity
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Latest system events and alerts
            </p>
          </div>
          <div className="card-body">
            <RecentActivity activities={mockRecentActivity} />
          </div>
        </div>

        {/* Top Risks */}
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">
              Top Risk Entities
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Highest scoring entities requiring attention
            </p>
          </div>
          <div className="card-body">
            <TopRisks risks={mockTopRisks} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
