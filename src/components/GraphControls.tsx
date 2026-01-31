import React from 'react';

interface GraphControlsProps {
  layout: string;
  onLayoutChange: (layout: string) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitToScreen: () => void;
}

const GraphControls: React.FC<GraphControlsProps> = ({ layout, onLayoutChange, onZoomIn, onZoomOut, onFitToScreen }) => {
  return (
    <div className="absolute top-4 right-4 bg-white rounded-lg shadow-md p-2 space-y-2">
      <div className="text-xs text-gray-500 mb-2">Layout: {layout}</div>
      <div className="text-center text-gray-400 text-xs">
        Graph controls will be implemented here
      </div>
    </div>
  );
};

export default GraphControls;
