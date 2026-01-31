import React from 'react';
import { render, screen } from '@testing-library/react';
import { StatCard } from '../../components';

describe('StatCard Component', () => {
  const defaultProps = {
    title: 'Test Stat',
    value: '100',
    icon: 'test-icon',
  };

  it('renders stat card with title and value', () => {
    render(<StatCard {...defaultProps} />);
    
    expect(screen.getByText('Test Stat')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });

  it('renders with trend indicator when provided', () => {
    const propsWithTrend = {
      ...defaultProps,
      trend: { value: 5, isPositive: true },
    };
    
    render(<StatCard {...propsWithTrend} />);
    
    expect(screen.getByText('+5')).toBeInTheDocument();
  });

  it('applies correct CSS classes', () => {
    const { container } = render(<StatCard {...defaultProps} />);
    
    const cardElement = container.querySelector('.bg-white');
    expect(cardElement).toBeInTheDocument();
  });

  it('displays icon correctly', () => {
    render(<StatCard {...defaultProps} />);
    
    const iconElement = screen.getByTestId('stat-icon');
    expect(iconElement).toBeInTheDocument();
  });

  it('handles negative trend', () => {
    const propsWithNegativeTrend = {
      ...defaultProps,
      trend: { value: 5, isPositive: false },
    };
    
    render(<StatCard {...propsWithNegativeTrend} />);
    
    expect(screen.getByText('-5')).toBeInTheDocument();
  });
});
