import React from 'react';

const ScoringPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Scoring</h1>
        <p className="mt-1 text-sm text-gray-500">
          Run scoring engines and analyze risk scores
        </p>
      </div>
      
      <div className="card">
        <div className="card-body">
          <div className="text-center py-12">
            <h3 className="text-lg font-medium text-gray-900">Scoring Interface</h3>
            <p className="mt-2 text-sm text-gray-500">
              Scoring engine interface will be implemented here.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ScoringPage;
