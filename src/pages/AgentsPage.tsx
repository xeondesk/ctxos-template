import React from 'react';

const AgentsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Agents</h1>
        <p className="mt-1 text-sm text-gray-500">
          Run AI agents and analysis pipelines
        </p>
      </div>
      
      <div className="card">
        <div className="card-body">
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900">Agent Management</h3>
            <p className="mt-2 text-sm text-gray-500">
              AI agent management interface will be implemented here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentsPage;
