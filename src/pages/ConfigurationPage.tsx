import React from 'react';

const ConfigurationPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configuration</h1>
        <p className="mt-1 text-sm text-gray-500">
          Manage system configuration and scoring rules
        </p>
      </div>
      
      <div className="card">
        <div className="card-body">
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900">Configuration Management</h3>
            <p className="mt-2 text-sm text-gray-500">
              Configuration management interface will be implemented here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationPage;
