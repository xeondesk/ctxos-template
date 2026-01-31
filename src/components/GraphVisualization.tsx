import React from 'react';

interface GraphVisualizationProps {
  data: { nodes: any[]; edges: any[] };
  layout: string;
  onNodeClick: (node: any) => void;
  selectedNodeId?: string;
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({ data, layout, onNodeClick, selectedNodeId }) => {
  return (
    <div className="h-full flex items-center justify-center bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg">
      <div className="text-center">
        <div className="text-lg font-medium text-gray-900">Graph Visualization</div>
        <div className="text-sm text-gray-500 mt-2">
          Interactive graph visualization will be implemented here
        </div>
        <div className="text-xs text-gray-400 mt-1">
          Layout: {layout} | Nodes: {data.nodes.length} | Edges: {data.edges.length}
        </div>
      </div>
    </div>
  );
};

export default GraphVisualization;
