# Frontend Testing Guide

## Overview

This guide covers the comprehensive testing setup for the CtxOS frontend application using Jest and React Testing Library.

## Test Structure

```
src/
├── __tests__/
│   ├── components/          # Component tests
│   ├── pages/              # Page component tests
│   ├── hooks/              # Custom hook tests
│   ├── utils/              # Test utilities and mocks
│   └── integration/        # Integration tests
├── setupTests.ts           # Global test setup
└── test-utils.tsx          # Custom test utilities
```

## Testing Stack

- **Jest** - Test runner and assertion library
- **React Testing Library** - Component testing utilities
- **React Query Test Utils** - State management testing
- **Jest DOM** - Custom DOM matchers
- **MSW (Mock Service Worker)** - API mocking (recommended for integration tests)

## Configuration Files

### jest.config.js
- Configures Jest with TypeScript support
- Sets up coverage thresholds
- Configures test environment and transforms

### babel.config.js
- Configures Babel for JSX and TypeScript transformation
- Sets up presets for React and modern JavaScript

### setupTests.ts
- Global test setup and mocks
- Configures testing-library extensions
- Sets up browser API mocks

## Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# Run specific test file
npm test -- StatCard.test.tsx

# Run tests matching a pattern
npm test -- --testNamePattern="renders"
```

## Test Types

### 1. Unit Tests

Test individual components and functions in isolation.

**Example: Component Test**
```typescript
import { render, screen } from '@testing-library/react';
import { StatCard } from '../components';

describe('StatCard Component', () => {
  it('renders title and value', () => {
    render(<StatCard title="Test" value="100" icon="test" />);
    
    expect(screen.getByText('Test')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
  });
});
```

### 2. Integration Tests

Test how multiple components work together.

**Example: Page Integration Test**
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import DashboardPage from '../pages/DashboardPage';

describe('DashboardPage Integration', () => {
  it('navigates between sections', async () => {
    render(
      <BrowserRouter>
        <DashboardPage />
      </BrowserRouter>
    );

    const graphTab = screen.getByText('Graph Explorer');
    fireEvent.click(graphTab);

    expect(screen.getByText('Graph Visualization')).toBeInTheDocument();
  });
});
```

### 3. Hook Tests

Test custom hooks using `renderHook`.

**Example: Hook Test**
```typescript
import { renderHook } from '@testing-library/react';
import { useAuthStore } from '../store/authStore';

describe('useAuthStore', () => {
  it('provides login function', () => {
    const { result } = renderHook(() => useAuthStore());
    
    expect(typeof result.current.login).toBe('function');
  });
});
```

## Best Practices

### 1. Test Structure

- **Arrange**: Set up test data and mocks
- **Act**: Perform the action being tested
- **Assert**: Verify the expected outcome

```typescript
it('handles user login', async () => {
  // Arrange
  const mockLogin = jest.fn();
  jest.mock('../store/authStore', () => ({
    useAuthStore: () => ({ login: mockLogin }),
  }));

  // Act
  const { result } = renderHook(() => useAuthStore());
  await result.current.login({ username: 'test', password: 'pass' });

  // Assert
  expect(mockLogin).toHaveBeenCalledWith({ username: 'test', password: 'pass' });
});
```

### 2. Component Testing Guidelines

- **Test behavior, not implementation**
- **Use accessible queries** (getByRole, getByLabelText)
- **Mock external dependencies**
- **Test user interactions**

```typescript
// Good: Test what the user sees and does
expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
fireEvent.click(screen.getByRole('button', { name: /submit/i }));

// Avoid: Test implementation details
expect(container.querySelector('.submit-button')).toBeTruthy();
```

### 3. Mocking Strategy

- **Mock API calls** for isolated component tests
- **Mock stores and contexts** for pure component testing
- **Use MSW** for realistic API integration tests

```typescript
// Mock API call
jest.mock('../api', () => ({
  fetchUser: jest.fn().mockResolvedValue({ id: 1, name: 'Test' }),
}));

// Mock store
jest.mock('../store/authStore', () => ({
  useAuthStore: () => ({
    user: { id: 1, name: 'Test' },
    login: jest.fn(),
  }),
}));
```

### 4. Test Data Management

- **Use consistent mock data**
- **Create reusable test utilities**
- **Keep test data minimal but realistic**

```typescript
// test-utils.tsx
export const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
};

// In test
import { mockUser } from '../utils/test-utils';
```

## Coverage Requirements

- **Branches**: 70%
- **Functions**: 70%
- **Lines**: 70%
- **Statements**: 70%

### Coverage Exclusions

- Test files (`**/*.test.tsx`, `**/*.spec.tsx`)
- Configuration files (`**/*.config.js`)
- Type definition files (`**/*.d.ts`)
- Entry points (`src/index.tsx`, `src/setupTests.ts`)

## Common Testing Patterns

### 1. Form Testing

```typescript
it('submits form with validation', async () => {
  const user = userEvent.setup();
  render(<LoginForm />);

  // Fill form
  await user.type(screen.getByLabelText(/username/i), 'testuser');
  await user.type(screen.getByLabelText(/password/i), 'password123');
  
  // Submit
  await user.click(screen.getByRole('button', { name: /submit/i }));

  // Assert
  expect(mockLogin).toHaveBeenCalledWith({
    username: 'testuser',
    password: 'password123',
  });
});
```

### 2. Async Component Testing

```typescript
it('loads and displays data', async () => {
  jest.mock('../api', () => ({
    fetchData: jest.fn().mockResolvedValue({ items: [] }),
  }));

  render(<DataComponent />);

  // Loading state
  expect(screen.getByText(/loading/i)).toBeInTheDocument();

  // Wait for data
  await waitFor(() => {
    expect(screen.getByText(/data loaded/i)).toBeInTheDocument();
  });
});
```

### 3. Error Handling Testing

```typescript
it('displays error message', async () => {
  jest.mock('../api', () => ({
    fetchData: jest.fn().mockRejectedValue(new Error('API Error')),
  }));

  render(<DataComponent />);

  await waitFor(() => {
    expect(screen.getByText(/api error/i)).toBeInTheDocument();
  });
});
```

## Debugging Tests

### 1. Screen Debugging

```typescript
import { screen } from '@testing-library/react';

// Print DOM structure
screen.debug();

// Print specific element
screen.debug(screen.getByTestId('user-form'));
```

### 2. Logging

```typescript
it('debug test', () => {
  console.log('Test data:', mockData);
  render(<Component />);
  console.log('Component rendered');
});
```

### 3. Test Breakpoints

```typescript
it('pause test', () => {
  render(<Component />);
  screen.debug();
  // Test will pause here
  expect(true).toBe(true);
});
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Frontend Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test:coverage
      - uses: codecov/codecov-action@v3
```

## Performance Testing

### Component Rendering Performance

```typescript
import { render } from '@testing-library/react';
import { performance } from 'perf_hooks';

it('renders efficiently', () => {
  const start = performance.now();
  render(<ComplexComponent />);
  const end = performance.now();
  
  expect(end - start).toBeLessThan(100); // 100ms threshold
});
```

## Accessibility Testing

### Using jest-axe

```typescript
import { axe, toHaveNoViolations } from 'jest-axe';
import { render } from '@testing-library/react';

expect.extend(toHaveNoViolations);

it('has no accessibility violations', async () => {
  const { container } = render(<Component />);
  const results = await axe(container);
  
  expect(results).toHaveNoViolations();
});
```

## Troubleshooting

### Common Issues

1. **"act" warnings**: Wrap state updates in `act()`
2. **Mock not working**: Check mock placement and import order
3. **Async test timeouts**: Use proper async/await patterns
4. **Coverage not accurate**: Check exclusions and test paths

### Solutions

```typescript
// Fix act warnings
import { act } from 'react-dom/test-utils';

act(() => {
  render(<Component />);
});

// Fix async issues
it('handles async', async () => {
  render(<Component />);
  await waitFor(() => {
    expect(screen.getByText('loaded')).toBeInTheDocument();
  });
});
```

## Resources

- [React Testing Library Docs](https://testing-library.com/docs/react-testing-library/intro)
- [Jest Docs](https://jestjs.io/docs/getting-started)
- [React Query Testing](https://tanstack.com/query/latest/docs/react/testing)
- [MSW Docs](https://mswjs.io/docs/getting-started)
