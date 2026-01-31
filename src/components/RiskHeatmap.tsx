import React from 'react';

interface RiskHeatmapProps {
  data: Array<{
    id: string;
    entityName: string;
    entityType: string;
    score: number;
    severity: string;
    impact: string;
    likelihood: string;
  }>;
  viewMode: 'grid' | 'table';
}

const RiskHeatmap: React.FC<RiskHeatmapProps> = ({ data, viewMode }) => {
  return (
    <div className="h-full flex items-center justify-center bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg">
      <div className="text-center">
        <div className="text-lg font-medium text-gray-900">Risk Heatmap</div>
        <div className="text-sm text-gray-500 mt-2">
          Risk heatmap visualization will be implemented here
        </div>
        <div className="text-xs text-gray-400 mt-1">
          View: {viewMode} | Entities: {data.length}
        </div>
      </div>
    </div>
  );
};

export default RiskHeatmap;
