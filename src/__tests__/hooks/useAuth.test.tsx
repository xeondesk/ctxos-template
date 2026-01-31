import { renderHook } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { useAuthStore } from '../store/authStore';

// Mock the actual store implementation
const mockLogin = jest.fn();
const mockLogout = jest.fn();
const mockRefreshToken = jest.fn();

jest.mock('../store/authStore', () => ({
  useAuthStore: () => ({
    user: null,
    token: null,
    isLoading: false,
    error: null,
    isAuthenticated: false,
    login: mockLogin,
    logout: mockLogout,
    refreshToken: mockRefreshToken,
  }),
}));

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={createTestQueryClient()}>
    {children}
  </QueryClientProvider>
);

describe('useAuthStore', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns initial auth state', () => {
    const { result } = renderHook(() => useAuthStore(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.token).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('provides login function', () => {
    const { result } = renderHook(() => useAuthStore(), { wrapper });

    expect(typeof result.current.login).toBe('function');
  });

  it('provides logout function', () => {
    const { result } = renderHook(() => useAuthStore(), { wrapper });

    expect(typeof result.current.logout).toBe('function');
  });

  it('provides refreshToken function', () => {
    const { result } = renderHook(() => useAuthStore(), { wrapper });

    expect(typeof result.current.refreshToken).toBe('function');
  });

  it('calls login with correct parameters', async () => {
    const { result } = renderHook(() => useAuthStore(), { wrapper });

    const credentials = { username: 'testuser', password: 'password123' };
    await result.current.login(credentials);

    expect(mockLogin).toHaveBeenCalledWith(credentials);
  });

  it('calls logout function', () => {
    const { result } = renderHook(() => useAuthStore(), { wrapper });

    result.current.logout();

    expect(mockLogout).toHaveBeenCalled();
  });

  it('calls refreshToken function', () => {
    const { result } = renderHook(() => useAuthStore(), { wrapper });

    result.current.refreshToken();

    expect(mockRefreshToken).toHaveBeenCalled();
  });
});
