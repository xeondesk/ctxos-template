import React from 'react';

interface RecentActivityProps {
  activities: Array<{
    id: string;
    type: string;
    message: string;
    timestamp: string;
    severity: string;
  }>;
}

const RecentActivity: React.FC<RecentActivityProps> = ({ activities }) => {
  return (
    <div className="space-y-3">
      {activities.slice(0, 5).map((activity) => (
        <div key={activity.id} className="flex items-center space-x-3 text-sm">
          <div className="flex-shrink-0">
            <div className="h-2 w-2 bg-gray-400 rounded-full"></div>
          </div>
          <div className="flex-1">
            <div className="text-gray-900">{activity.message}</div>
            <div className="text-gray-500 text-xs">
              {new Date(activity.timestamp).toLocaleString()}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default RecentActivity;
