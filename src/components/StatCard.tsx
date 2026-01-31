import React from 'react';

interface StatCardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  loading?: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon, trend, loading }) => {
  return (
    <div className="stat-card">
      <div className="card-body p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-8 w-8 text-primary-600">
              {icon}
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="stat-card-value">
                {loading ? (
                  <div className="loading-spinner h-6 w-6"></div>
                ) : (
                  value
                )}
              </dd>
            </dl>
          </div>
        </div>
        {trend && (
          <div className="mt-4 flex items-center">
            <span
              className={`text-sm font-medium ${
                trend.isPositive ? 'text-green-600' : 'text-red-600'
              }`}
            >
              {trend.isPositive ? '+' : '-'}{trend.value}%
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default StatCard;
