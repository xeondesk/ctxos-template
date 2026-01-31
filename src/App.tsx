import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { useAuthStore } from 'store';
import { apiClient } from 'api';

// Layout Components
import Layout from 'components/Layout';
import AuthLayout from 'components/AuthLayout';

// Page Components
import LoginPage from 'pages/LoginPage';
import DashboardPage from 'pages/DashboardPage';
import GraphExplorerPage from 'pages/GraphExplorerPage';
import RiskHeatmapPage from 'pages/RiskHeatmapPage';
import EntitiesPage from 'pages/EntitiesPage';
import ScoringPage from 'pages/ScoringPage';
import AgentsPage from 'pages/AgentsPage';
import ConfigurationPage from 'pages/ConfigurationPage';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

// Public Route Component (redirect if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
};

// App Component
const App: React.FC = () => {
  const { token, isAuthenticated } = useAuthStore();

  // Set API client token when it changes
  useEffect(() => {
    if (token) {
      apiClient.setToken(token);
    } else {
      apiClient.setToken(null);
    }
  }, [token]);

  // Verify token on app load if authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      apiClient.verifyToken().catch(() => {
        // Token is invalid, clear auth state
        useAuthStore.getState().logout();
      });
    }
  }, [isAuthenticated, token]);

  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Routes>
            {/* Public Routes */}
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <AuthLayout>
                    <LoginPage />
                  </AuthLayout>
                </PublicRoute>
              }
            />

            {/* Protected Routes */}
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="graph" element={<GraphExplorerPage />} />
              <Route path="risk" element={<RiskHeatmapPage />} />
              <Route path="entities" element={<EntitiesPage />} />
              <Route path="scoring" element={<ScoringPage />} />
              <Route path="agents" element={<AgentsPage />} />
              <Route path="configuration" element={<ConfigurationPage />} />
            </Route>

            {/* Catch all route */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </QueryClientProvider>
  );
};

export default App;
