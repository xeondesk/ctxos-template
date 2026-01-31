import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import LoginPage from '../../pages/LoginPage';
import { AuthLayout } from '../../components';

// Mock the auth store
jest.mock('../../store/authStore', () => ({
  useAuthStore: () => ({
    login: jest.fn(),
    isLoading: false,
    error: null,
  }),
}));

const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const renderWithProviders = (component: React.ReactElement) => {
  const testQueryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={testQueryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders login form elements', () => {
    renderWithProviders(
      <AuthLayout>
        <LoginPage />
      </AuthLayout>
    );

    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument();
  });

  it('shows password when toggle is clicked', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <AuthLayout>
        <LoginPage />
      </AuthLayout>
    );

    const passwordInput = screen.getByLabelText(/password/i);
    const toggleButton = screen.getByRole('button', { name: /show password/i });

    expect(passwordInput).toHaveAttribute('type', 'password');

    await user.click(toggleButton);

    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument();
  });

  it('validates form inputs', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(
      <AuthLayout>
        <LoginPage />
      </AuthLayout>
    );

    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.click(submitButton);

    // Should show validation errors for empty fields
    await waitFor(() => {
      expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it('submits form with valid credentials', async () => {
    const mockLogin = jest.fn();
    jest.mock('../../store/authStore', () => ({
      useAuthStore: () => ({
        login: mockLogin,
        isLoading: false,
        error: null,
      }),
    }));

    const user = userEvent.setup();
    
    renderWithProviders(
      <AuthLayout>
        <LoginPage />
      </AuthLayout>
    );

    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'password123');
    await user.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });
  });

  it('displays error message when login fails', async () => {
    const mockLogin = jest.fn().mockRejectedValue(new Error('Invalid credentials'));
    jest.mock('../../store/authStore', () => ({
      useAuthStore: () => ({
        login: mockLogin,
        isLoading: false,
        error: 'Invalid credentials',
      }),
    }));

    renderWithProviders(
      <AuthLayout>
        <LoginPage />
      </AuthLayout>
    );

    expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
  });

  it('shows loading state during login', async () => {
    jest.mock('../../store/authStore', () => ({
      useAuthStore: () => ({
        login: jest.fn(),
        isLoading: true,
        error: null,
      }),
    }));

    renderWithProviders(
      <AuthLayout>
        <LoginPage />
      </AuthLayout>
    );

    const submitButton = screen.getByRole('button', { name: /sign in/i });
    expect(submitButton).toBeDisabled();
    expect(screen.getByText(/signing in/i)).toBeInTheDocument();
  });
});
