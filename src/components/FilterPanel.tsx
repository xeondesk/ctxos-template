import React from 'react';

interface FilterPanelProps {
  filter: any;
  onFilterChange: (filter: any) => void;
}

const FilterPanel: React.FC<FilterPanelProps> = ({ filter, onFilterChange }) => {
  return (
    <div className="p-4 space-y-4">
      <h3 className="text-lg font-medium text-gray-900">Filters</h3>
      <div className="text-center text-gray-500 text-sm">
        Filter panel will be implemented here
      </div>
    </div>
  );
};

export default FilterPanel;
