import React, { useState, useMemo } from 'react';
import { useQuery } from 'react-query';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
} from '@heroicons/react/24/outline';
import { EntityType, SeverityLevel, EntityFilter } from '@/types';
import { apiClient } from '@/api';

// Components
import RiskHeatmap from '@/components/RiskHeatmap';
import RiskDetails from '@/components/RiskDetails';
import FilterPanel from '@/components/FilterPanel';

const RiskHeatmapPage: React.FC = () => {
  // State
  const [selectedEntity, setSelectedEntity] = useState<any>(null);
  const [filter, setFilter] = useState<EntityFilter>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');

  // Mock data for demonstration
  const mockRiskData = [
    {
      id: 'web-server-01',
      name: 'web-server-01',
      type: 'host' as EntityType,
      score: 92,
      severity: 'critical' as SeverityLevel,
      ip: '192.168.1.100',
      environment: 'production',
      lastScanned: '2024-01-15T10:30:00Z',
      vulnerabilities: 15,
      openPorts: 8,
      topIssues: ['CVE-2023-1234', 'Apache Struts RCE', 'SSL Certificate Expired'],
    },
    {
      id: 'api.example.com',
      name: 'api.example.com',
      type: 'domain' as EntityType,
      score: 85,
      severity: 'high' as SeverityLevel,
      registrar: 'GoDaddy',
      expires: '2024-06-15',
      environment: 'production',
      lastScanned: '2024-01-15T09:45:00Z',
      vulnerabilities: 8,
      subdomains: 12,
      topIssues: ['Subdomain Takeover Risk', 'DNS Misconfiguration', 'Outdated SSL'],
    },
    {
      id: 'db-server-01',
      name: 'db-server-01',
      type: 'host' as EntityType,
      score: 78,
      severity: 'medium' as SeverityLevel,
      ip: '192.168.1.200',
      environment: 'production',
      lastScanned: '2024-01-15T08:20:00Z',
      vulnerabilities: 5,
      openPorts: 3,
      topIssues: ['MySQL Vulnerability', 'Weak Authentication', 'Backup Exposure'],
    },
    {
      id: 'admin-user',
      name: 'admin-user',
      type: 'user' as EntityType,
      score: 65,
      severity: 'medium' as SeverityLevel,
      role: 'administrator',
      lastLogin: '2024-01-15T07:30:00Z',
      environment: 'production',
      lastScanned: '2024-01-14T16:45:00Z',
      failedLogins: 3,
      topIssues: ['Weak Password Policy', 'MFA Disabled', 'Privilege Escalation Risk'],
    },
    {
      id: 'vpn-gateway',
      name: 'vpn-gateway',
      type: 'host' as EntityType,
      score: 58,
      severity: 'medium' as SeverityLevel,
      ip: '192.168.1.1',
      environment: 'production',
      lastScanned: '2024-01-15T06:15:00Z',
      vulnerabilities: 3,
      openPorts: 2,
      topIssues: ['Outdated Firmware', 'Open Management Port', 'Weak VPN Configuration'],
    },
    {
      id: 'test-server-01',
      name: 'test-server-01',
      type: 'host' as EntityType,
      score: 45,
      severity: 'low' as SeverityLevel,
      ip: '192.168.2.100',
      environment: 'staging',
      lastScanned: '2024-01-15T05:30:00Z',
      vulnerabilities: 2,
      openPorts: 4,
      topIssues: ['Test Credentials', 'Debug Mode Enabled'],
    },
    {
      id: 'backup-server',
      name: 'backup-server',
      type: 'host' as EntityType,
      score: 38,
      severity: 'low' as SeverityLevel,
      ip: '192.168.1.50',
      environment: 'production',
      lastScanned: '2024-01-14T22:10:00Z',
      vulnerabilities: 1,
      openPorts: 2,
      topIssues: ['Unencrypted Backups'],
    },
    {
      id: 'monitoring.example.com',
      name: 'monitoring.example.com',
      type: 'domain' as EntityType,
      score: 32,
      severity: 'low' as SeverityLevel,
      registrar: 'Namecheap',
      expires: '2024-12-01',
      environment: 'production',
      lastScanned: '2024-01-14T20:45:00Z',
      subdomains: 3,
      topIssues: ['Missing SPF Record'],
    },
  ];

  // Filter and search data
  const filteredData = useMemo(() => {
    let filtered = [...mockRiskData];

    // Apply search query
    if (searchQuery) {
      filtered = filtered.filter(item =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply entity type filter
    if (filter.entity_types && filter.entity_types.length > 0) {
      filtered = filtered.filter(item =>
        filter.entity_types!.includes(item.type)
      );
    }

    // Apply severity filter
    if (filter.severity_levels && filter.severity_levels.length > 0) {
      filtered = filtered.filter(item =>
        filter.severity_levels!.includes(item.severity)
      );
    }

    // Apply score range filter
    if (filter.score_range) {
      const [minScore, maxScore] = filter.score_range;
      filtered = filtered.filter(item =>
        item.score >= minScore && item.score <= maxScore
      );
    }

    // Apply environment filter
    if (filter.search_query && filter.search_query.includes('environment:')) {
      const env = filter.search_query.split('environment:')[1].trim();
      filtered = filtered.filter(item => item.environment === env);
    }

    return filtered;
  }, [mockRiskData, searchQuery, filter]);

  // Calculate statistics
  const statistics = useMemo(() => {
    const total = filteredData.length;
    const critical = filteredData.filter(item => item.severity === 'critical').length;
    const high = filteredData.filter(item => item.severity === 'high').length;
    const medium = filteredData.filter(item => item.severity === 'medium').length;
    const low = filteredData.filter(item => item.severity === 'low').length;
    const avgScore = filteredData.reduce((sum, item) => sum + item.score, 0) / total || 0;

    return {
      total,
      critical,
      high,
      medium,
      low,
      avgScore: Math.round(avgScore),
    };
  }, [filteredData]);

  const handleEntityClick = (entity: any) => {
    setSelectedEntity(entity);
  };

  const handleFilterChange = (newFilter: EntityFilter) => {
    setFilter(newFilter);
  };

  const handleExport = () => {
    const csvContent = [
      ['ID', 'Name', 'Type', 'Score', 'Severity', 'Environment', 'Last Scanned', 'Top Issues'].join(','),
      ...filteredData.map(item => [
        item.id,
        item.name,
        item.type,
        item.score,
        item.severity,
        item.environment,
        item.lastScanned,
        `"${item.topIssues.join('; ')}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ctxos-risk-heatmap.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getSeverityColor = (severity: SeverityLevel) => {
    switch (severity) {
      case 'critical': return 'bg-red-600';
      case 'high': return 'bg-orange-600';
      case 'medium': return 'bg-yellow-600';
      case 'low': return 'bg-blue-600';
      default: return 'bg-gray-600';
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Risk Heatmap</h1>
            <p className="mt-1 text-sm text-gray-500">
              Visualize risk scores across all entities and identify critical assets
            </p>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Search */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search entities..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="input pl-10 w-64"
              />
              <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
            </div>
            
            {/* View Mode Toggle */}
            <div className="flex rounded-md shadow-sm">
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 text-sm font-medium rounded-l-md border ${
                  viewMode === 'grid'
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Grid
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-3 py-2 text-sm font-medium rounded-r-md border-t border-r border-b ${
                  viewMode === 'table'
                    ? 'bg-primary-600 text-white border-primary-600'
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                Table
              </button>
            </div>
            
            {/* Controls */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="btn btn-secondary"
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filters
            </button>
            
            <button
              onClick={handleExport}
              className="btn btn-secondary"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Bar */}
      <div className="bg-gray-50 border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div className="text-sm">
              <span className="font-medium text-gray-900">Total Entities:</span>
              <span className="ml-2 text-gray-600">{statistics.total}</span>
            </div>
            <div className="flex items-center text-sm">
              <span className="font-medium text-gray-900">Average Score:</span>
              <span className="ml-2 text-gray-600">{statistics.avgScore}</span>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center">
                <div className="h-2 w-2 bg-red-600 rounded-full mr-1"></div>
                Critical: {statistics.critical}
              </div>
              <div className="flex items-center">
                <div className="h-2 w-2 bg-orange-600 rounded-full mr-1"></div>
                High: {statistics.high}
              </div>
              <div className="flex items-center">
                <div className="h-2 w-2 bg-yellow-600 rounded-full mr-1"></div>
                Medium: {statistics.medium}
              </div>
              <div className="flex items-center">
                <div className="h-2 w-2 bg-blue-600 rounded-full mr-1"></div>
                Low: {statistics.low}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Filter Panel */}
        {showFilters && (
          <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
            <FilterPanel
              filter={filter}
              onFilterChange={handleFilterChange}
            />
          </div>
        )}

        {/* Risk Visualization */}
        <div className="flex-1 p-6">
          {viewMode === 'grid' ? (
            <RiskHeatmap
              data={filteredData}
              onEntityClick={handleEntityClick}
              selectedEntityId={selectedEntity?.id}
            />
          ) : (
            <div className="card">
              <div className="card-body p-0">
                <table className="table">
                  <thead className="table-header">
                    <tr>
                      <th className="table-header-cell">Entity</th>
                      <th className="table-header-cell">Type</th>
                      <th className="table-header-cell">Score</th>
                      <th className="table-header-cell">Severity</th>
                      <th className="table-header-cell">Environment</th>
                      <th className="table-header-cell">Last Scanned</th>
                      <th className="table-header-cell">Top Issues</th>
                    </tr>
                  </thead>
                  <tbody className="table-body">
                    {filteredData.map((item) => (
                      <tr
                        key={item.id}
                        className="table-row cursor-pointer hover:bg-gray-50"
                        onClick={() => handleEntityClick(item)}
                      >
                        <td className="table-cell">
                          <div>
                            <div className="font-medium text-gray-900">{item.name}</div>
                            <div className="text-sm text-gray-500">{item.id}</div>
                          </div>
                        </td>
                        <td className="table-cell">
                          <span className="badge badge-info">{item.type}</span>
                        </td>
                        <td className="table-cell">
                          <div className="flex items-center">
                            <div className="text-sm font-medium text-gray-900">{item.score}</div>
                            <div className="ml-2 w-16 bg-gray-200 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full ${getSeverityColor(item.severity)}`}
                                style={{ width: `${item.score}%` }}
                              ></div>
                            </div>
                          </div>
                        </td>
                        <td className="table-cell">
                          <span className={`badge badge-${item.severity}`}>
                            {item.severity}
                          </span>
                        </td>
                        <td className="table-cell">
                          <span className="badge badge-info">{item.environment}</span>
                        </td>
                        <td className="table-cell text-sm text-gray-500">
                          {new Date(item.lastScanned).toLocaleDateString()}
                        </td>
                        <td className="table-cell">
                          <div className="text-sm text-gray-900">
                            {item.topIssues.slice(0, 2).map((issue, index) => (
                              <div key={index} className="truncate">
                                {issue}
                              </div>
                            ))}
                            {item.topIssues.length > 2 && (
                              <div className="text-gray-500">+{item.topIssues.length - 2} more</div>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* Entity Details Panel */}
        {selectedEntity && (
          <div className="w-96 bg-white border-l border-gray-200 overflow-y-auto">
            <RiskDetails
              entity={selectedEntity}
              onClose={() => setSelectedEntity(null)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default RiskHeatmapPage;
