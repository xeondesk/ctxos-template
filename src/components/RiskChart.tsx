import React from 'react';

interface RiskChartProps {
  data: Array<{ name: string; value: number; color: string }>;
}

const RiskChart: React.FC<RiskChartProps> = ({ data }) => {
  return (
    <div className="h-64 flex items-center justify-center">
      <div className="text-center">
        <div className="text-sm text-gray-500">Risk Distribution Chart</div>
        <div className="text-xs text-gray-400 mt-2">
          Chart visualization will be implemented here
        </div>
      </div>
    </div>
  );
};

export default RiskChart;
