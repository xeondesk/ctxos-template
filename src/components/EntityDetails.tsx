import React from 'react';

interface EntityDetailsProps {
  entity: any;
  onClose: () => void;
}

const EntityDetails: React.FC<EntityDetailsProps> = ({ entity, onClose }) => {
  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Entity Details</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ×
          </button>
        </div>
      </div>
      <div className="flex-1 p-4">
        <div className="text-center text-gray-500">
          Entity details panel will be implemented here
        </div>
      </div>
    </div>
  );
};

export default EntityDetails;
