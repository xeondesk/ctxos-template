import React, { useState, useCallback } from 'react';
import { useQuery } from 'react-query';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline';
import { GraphNode, GraphEdge, EntityFilter } from '@/types';
import { apiClient } from '@/api';

// Components
import GraphVisualization from '@/components/GraphVisualization';
import EntityDetails from '@/components/EntityDetails';
import FilterPanel from '@/components/FilterPanel';
import GraphControls from '@/components/GraphControls';

const GraphExplorerPage: React.FC = () => {
  // State
  const [selectedEntity, setSelectedEntity] = useState<GraphNode | null>(null);
  const [filter, setFilter] = useState<EntityFilter>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [layout, setLayout] = useState<'force' | 'hierarchical' | 'circular'>('force');
  const [showFilters, setShowFilters] = useState(false);

  // Mock data for demonstration
  const mockGraphData = {
    nodes: [
      {
        id: 'web-server-01',
        type: 'host',
        label: 'web-server-01',
        data: {
          entity: {
            id: 'web-server-01',
            entity_type: 'host',
            name: 'web-server-01',
            properties: {
              ip: '192.168.1.100',
              os: 'Ubuntu 20.04',
              environment: 'production'
            }
          },
          score: 92,
          severity: 'critical'
        },
        style: {
          backgroundColor: '#dc2626',
          color: '#ffffff'
        }
      },
      {
        id: 'api.example.com',
        type: 'domain',
        label: 'api.example.com',
        data: {
          entity: {
            id: 'api.example.com',
            entity_type: 'domain',
            name: 'api.example.com',
            properties: {
              registrar: 'GoDaddy',
              expires: '2024-06-15'
            }
          },
          score: 85,
          severity: 'high'
        },
        style: {
          backgroundColor: '#f59e0b',
          color: '#ffffff'
        }
      },
      {
        id: 'db-server-01',
        type: 'host',
        label: 'db-server-01',
        data: {
          entity: {
            id: 'db-server-01',
            entity_type: 'host',
            name: 'db-server-01',
            properties: {
              ip: '192.168.1.200',
              os: 'CentOS 8',
              environment: 'production'
            }
          },
          score: 78,
          severity: 'medium'
        },
        style: {
          backgroundColor: '#eab308',
          color: '#ffffff'
        }
      },
      {
        id: 'admin-user',
        type: 'user',
        label: 'admin-user',
        data: {
          entity: {
            id: 'admin-user',
            entity_type: 'user',
            name: 'admin-user',
            properties: {
              role: 'administrator',
              last_login: '2024-01-15T09:30:00Z'
            }
          },
          score: 45,
          severity: 'low'
        },
        style: {
          backgroundColor: '#3b82f6',
          color: '#ffffff'
        }
      },
      {
        id: 'vpn-gateway',
        type: 'host',
        label: 'vpn-gateway',
        data: {
          entity: {
            id: 'vpn-gateway',
            entity_type: 'host',
            name: 'vpn-gateway',
            properties: {
              ip: '192.168.1.1',
              os: 'pfSense',
              environment: 'production'
            }
          },
          score: 65,
          severity: 'medium'
        },
        style: {
          backgroundColor: '#eab308',
          color: '#ffffff'
        }
      }
    ] as GraphNode[],
    edges: [
      {
        id: 'edge-1',
        source: 'web-server-01',
        target: 'api.example.com',
        type: 'hosts',
        data: {
          relationship: 'hosts',
          confidence: 0.95
        },
        style: {
          stroke: '#6b7280',
          strokeWidth: 2
        }
      },
      {
        id: 'edge-2',
        source: 'web-server-01',
        target: 'db-server-01',
        type: 'connects_to',
        data: {
          relationship: 'database_connection',
          port: 5432
        },
        style: {
          stroke: '#6b7280',
          strokeWidth: 2
        }
      },
      {
        id: 'edge-3',
        source: 'admin-user',
        target: 'web-server-01',
        type: 'accesses',
        data: {
          relationship: 'ssh_access',
          last_access: '2024-01-15T08:45:00Z'
        },
        style: {
          stroke: '#6b7280',
          strokeWidth: 2
        }
      },
      {
        id: 'edge-4',
        source: 'admin-user',
        target: 'db-server-01',
        type: 'accesses',
        data: {
          relationship: 'database_access',
          last_access: '2024-01-14T16:20:00Z'
        },
        style: {
          stroke: '#6b7280',
          strokeWidth: 2
        }
      },
      {
        id: 'edge-5',
        source: 'web-server-01',
        target: 'vpn-gateway',
        type: 'routes_through',
        data: {
          relationship: 'network_route',
          protocol: 'https'
        },
        style: {
          stroke: '#6b7280',
          strokeWidth: 2
        }
      }
    ] as GraphEdge[]
  };

  // Filter graph data based on search and filters
  const filteredGraphData = useCallback(() => {
    let filteredNodes = [...mockGraphData.nodes];
    let filteredEdges = [...mockGraphData.edges];

    // Apply search query
    if (searchQuery) {
      filteredNodes = filteredNodes.filter(node =>
        node.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
        node.data.entity.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Apply entity type filter
    if (filter.entity_types && filter.entity_types.length > 0) {
      filteredNodes = filteredNodes.filter(node =>
        filter.entity_types!.includes(node.data.entity.entity_type)
      );
    }

    // Apply severity filter
    if (filter.severity_levels && filter.severity_levels.length > 0) {
      filteredNodes = filteredNodes.filter(node =>
        filter.severity_levels!.includes(node.data.severity || 'info')
      );
    }

    // Apply score range filter
    if (filter.score_range) {
      const [minScore, maxScore] = filter.score_range;
      filteredNodes = filteredNodes.filter(node =>
        node.data.score >= minScore && node.data.score <= maxScore
      );
    }

    // Filter edges to only include connections between filtered nodes
    const nodeIds = new Set(filteredNodes.map(node => node.id));
    filteredEdges = filteredEdges.filter(edge =>
      nodeIds.has(edge.source) && nodeIds.has(edge.target)
    );

    return {
      nodes: filteredNodes,
      edges: filteredEdges
    };
  }, [mockGraphData, searchQuery, filter]);

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedEntity(node);
  }, []);

  const handleFilterChange = useCallback((newFilter: EntityFilter) => {
    setFilter(newFilter);
  }, []);

  const handleRefresh = useCallback(() => {
    // In a real implementation, this would refetch data
    console.log('Refreshing graph data...');
  }, []);

  const handleExport = useCallback(() => {
    // Export graph data as JSON
    const dataStr = JSON.stringify(filteredGraphData(), null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'ctxos-graph-export.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  }, [filteredGraphData]);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Graph Explorer</h1>
            <p className="mt-1 text-sm text-gray-500">
              Visualize relationships between entities and explore attack surface
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
            
            {/* Controls */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="btn btn-secondary"
            >
              <FunnelIcon className="h-4 w-4 mr-2" />
              Filters
            </button>
            
            <button
              onClick={handleRefresh}
              className="btn btn-secondary"
            >
              <ArrowPathIcon className="h-4 w-4 mr-2" />
              Refresh
            </button>
            
            <button
              onClick={handleExport}
              className="btn btn-secondary"
            >
              Export
            </button>
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

        {/* Graph Visualization */}
        <div className="flex-1 relative">
          <GraphControls
            layout={layout}
            onLayoutChange={setLayout}
            onZoomIn={() => console.log('Zoom in')}
            onZoomOut={() => console.log('Zoom out')}
            onFitToScreen={() => console.log('Fit to screen')}
          />
          
          <GraphVisualization
            data={filteredGraphData()}
            layout={layout}
            onNodeClick={handleNodeClick}
            selectedNodeId={selectedEntity?.id}
          />
        </div>

        {/* Entity Details Panel */}
        {selectedEntity && (
          <div className="w-96 bg-white border-l border-gray-200 overflow-y-auto">
            <EntityDetails
              entity={selectedEntity}
              onClose={() => setSelectedEntity(null)}
            />
          </div>
        )}
      </div>

      {/* Status Bar */}
      <div className="bg-gray-50 border-t border-gray-200 px-6 py-2">
        <div className="flex items-center justify-between text-sm text-gray-600">
          <div>
            Showing {filteredGraphData().nodes.length} nodes and {filteredGraphData().edges.length} edges
          </div>
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <div className="h-2 w-2 bg-red-600 rounded-full mr-1"></div>
              Critical: {filteredGraphData().nodes.filter(n => n.data.severity === 'critical').length}
            </div>
            <div className="flex items-center">
              <div className="h-2 w-2 bg-yellow-600 rounded-full mr-1"></div>
              High: {filteredGraphData().nodes.filter(n => n.data.severity === 'high').length}
            </div>
            <div className="flex items-center">
              <div className="h-2 w-2 bg-yellow-500 rounded-full mr-1"></div>
              Medium: {filteredGraphData().nodes.filter(n => n.data.severity === 'medium').length}
            </div>
            <div className="flex items-center">
              <div className="h-2 w-2 bg-blue-600 rounded-full mr-1"></div>
              Low: {filteredGraphData().nodes.filter(n => n.data.severity === 'low').length}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphExplorerPage;
