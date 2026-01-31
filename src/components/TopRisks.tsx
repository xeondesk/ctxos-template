import React from 'react';

interface TopRisksProps {
  risks: Array<{
    id: string;
    entityName: string;
    entityType: string;
    score: number;
    severity: string;
    topIssues: string[];
  }>;
}

const TopRisks: React.FC<TopRisksProps> = ({ risks }) => {
  return (
    <div className="space-y-3">
      {risks.slice(0, 5).map((risk) => (
        <div key={risk.id} className="border-l-4 border-red-500 pl-4 py-2">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium text-gray-900">{risk.entityName}</div>
              <div className="text-sm text-gray-500">{risk.entityType}</div>
            </div>
            <div className="text-right">
              <div className="font-bold text-lg">{risk.score}</div>
              <div className="text-xs text-gray-500">{risk.severity}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default TopRisks;
