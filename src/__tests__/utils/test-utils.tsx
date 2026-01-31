import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';

// Create a test query client
const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

// Custom render function that includes providers
const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const testQueryClient = createTestQueryClient();
  return (
    <QueryClientProvider client={testQueryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Mock data for testing
export const mockUser = {
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  role: 'admin',
  is_active: true,
};

export const mockTenant = {
  id: 1,
  name: 'Test Tenant',
  slug: 'test-tenant',
  description: 'A test tenant',
  status: 'active',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const mockProject = {
  id: 1,
  tenant_id: 1,
  name: 'Test Project',
  slug: 'test-project',
  description: 'A test project',
  status: 'active',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const mockEntity = {
  id: 'entity-1',
  type: 'domain',
  name: 'example.com',
  data: {
    ip: '192.168.1.1',
    subdomains: ['www', 'api', 'admin'],
  },
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

export const mockSignal = {
  id: 'signal-1',
  entity_id: 'entity-1',
  type: 'dns_record',
  data: {
    record_type: 'A',
    value: '192.168.1.1',
    ttl: 300,
  },
  confidence: 0.9,
  created_at: new Date().toISOString(),
};

// Mock API responses
export const mockApiResponse = (data: any, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {},
});

// Mock functions
export const mockLogin = jest.fn();
export const mockLogout = jest.fn();
export const mockRefreshToken = jest.fn();

// Re-export everything from testing-library
export * from '@testing-library/react';
export { customRender as render };

// Helper functions for testing
export const waitForElementToBeRemoved = (element: HTMLElement) => {
  return new Promise((resolve) => {
    if (!element || !element.parentNode) {
      resolve(null);
      return;
    }
    
    const observer = new MutationObserver(() => {
      if (!element.parentNode) {
        observer.disconnect();
        resolve(null);
      }
    });
    
    observer.observe(element.parentNode, {
      childList: true,
      subtree: true,
    });
  });
};

export const createMockEvent = (type: string, properties: any = {}) => {
  const event = new Event(type, { bubbles: true });
  Object.assign(event, properties);
  return event;
};

export const createMockFile = (name: string, type: string, size: number = 1024) => {
  const file = new File([''], name, { type });
  Object.defineProperty(file, 'size', { value: size });
  return file;
};
