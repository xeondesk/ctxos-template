import axios, { AxiosInstance, AxiosResponse } from 'axios';
import { 
  LoginRequest, 
  LoginResponse, 
  ScoreRequest, 
  ScoringResult, 
  BatchScoreRequest,
  AgentRunRequest,
  AgentResult,
  PipelineRunRequest,
  PipelineResult,
  ConfigUpdateRequest,
  RuleCreateRequest,
  HealthStatus,
  PaginatedResponse,
  Entity,
  Context
} from 'types';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor to handle common errors
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired, clear it and redirect to login
          this.setToken(null);
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string | null) {
    this.token = token;
  }

  getToken(): string | null {
    return this.token;
  }

  // Authentication endpoints
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response: AxiosResponse<LoginResponse> = await this.client.post(
      '/api/v1/auth/login',
      credentials
    );
    this.setToken(response.data.access_token);
    return response.data;
  }

  async logout(): Promise<void> {
    if (this.token) {
      try {
        await this.client.post('/api/v1/auth/logout');
      } catch (error) {
        // Ignore logout errors
      }
    }
    this.setToken(null);
  }

  async refreshToken(refreshToken: string): Promise<{ access_token: string }> {
    const response = await this.client.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    this.setToken(response.data.access_token);
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get('/api/v1/auth/me');
    return response.data;
  }

  async verifyToken(): Promise<{ valid: boolean }> {
    const response = await this.client.get('/api/v1/auth/verify');
    return response.data;
  }

  // Scoring endpoints
  async scoreEntity(request: ScoreRequest): Promise<ScoringResult[]> {
    const response = await this.client.post('/api/v1/score', request);
    return response.data;
  }

  async batchScore(request: BatchScoreRequest): Promise<ScoringResult[]> {
    const response = await this.client.post('/api/v1/score/batch', request);
    return response.data;
  }

  async getScoringHistory(
    entityId: string,
    params: {
      date_from: string;
      date_to: string;
      engines?: string[];
      granularity?: string;
      limit?: number;
    }
  ): Promise<PaginatedResponse<any>> {
    const response = await this.client.post(
      `/api/v1/score/history/${entityId}`,
      params
    );
    return response.data;
  }

  async getScoringEngines(): Promise<{ engines: Record<string, any> }> {
    const response = await this.client.get('/api/v1/score/engines');
    return response.data;
  }

  async getAggregateScores(request: {
    entity_ids: string[];
    engines: string[];
  }): Promise<any> {
    const response = await this.client.post('/api/v1/score/aggregate', request);
    return response.data;
  }

  async compareEntities(request: {
    entity_ids: string[];
    engines: string[];
  }): Promise<any> {
    const response = await this.client.post('/api/v1/score/compare', request);
    return response.data;
  }

  async getScoringStatus(): Promise<HealthStatus> {
    const response = await this.client.get('/api/v1/score/status');
    return response.data;
  }

  // Agent endpoints
  async runAgent(request: AgentRunRequest): Promise<AgentResult> {
    const response = await this.client.post('/api/v1/agents/run', request);
    return response.data;
  }

  async runPipeline(request: PipelineRunRequest): Promise<PipelineResult> {
    const response = await this.client.post('/api/v1/agents/pipeline', request);
    return response.data;
  }

  async bulkAnalysis(request: {
    entity_ids: string[];
    entity_type: string;
    engines: string[];
    agents: string[];
    parallel?: boolean;
    timeout_per_entity?: number;
  }): Promise<any> {
    const response = await this.client.post('/api/v1/agents/bulk', request);
    return response.data;
  }

  async listAgents(): Promise<{ agents: Record<string, any> }> {
    const response = await this.client.get('/api/v1/agents/list');
    return response.data;
  }

  async getAgentStatus(agentName: string): Promise<any> {
    const response = await this.client.get(`/api/v1/agents/status/${agentName}`);
    return response.data;
  }

  async listPipelines(): Promise<{ pipelines: Record<string, any> }> {
    const response = await this.client.get('/api/v1/agents/pipelines');
    return response.data;
  }

  async createPipeline(request: {
    pipeline_name: string;
    agents: string[];
    parallel?: boolean;
  }): Promise<any> {
    const response = await this.client.post('/api/v1/agents/create-pipeline', request);
    return response.data;
  }

  async getAgentMetrics(): Promise<any> {
    const response = await this.client.get('/api/v1/agents/metrics');
    return response.data;
  }

  async getAgentHealth(): Promise<HealthStatus> {
    const response = await this.client.get('/api/v1/agents/health');
    return response.data;
  }

  async getAgentAuditLogs(params: {
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<any>> {
    const response = await this.client.get('/api/v1/agents/audit-logs', { params });
    return response.data;
  }

  // Configuration endpoints
  async getConfig(): Promise<{ config: Record<string, any> }> {
    const response = await this.client.get('/api/v1/config');
    return response.data;
  }

  async getConfigValue(key: string): Promise<any> {
    const response = await this.client.get(`/api/v1/config/${key}`);
    return response.data;
  }

  async updateConfig(request: ConfigUpdateRequest): Promise<any> {
    const response = await this.client.post('/api/v1/config/update', request);
    return response.data;
  }

  async getRules(): Promise<{ rules: Record<string, any> }> {
    const response = await this.client.get('/api/v1/config/rules');
    return response.data;
  }

  async createRule(request: RuleCreateRequest): Promise<any> {
    const response = await this.client.post('/api/v1/config/rules', request);
    return response.data;
  }

  async getRule(ruleId: string): Promise<any> {
    const response = await this.client.get(`/api/v1/config/rules/${ruleId}`);
    return response.data;
  }

  async updateRule(ruleId: string, request: Partial<RuleCreateRequest>): Promise<any> {
    const response = await this.client.put(`/api/v1/config/rules/${ruleId}`, request);
    return response.data;
  }

  async deleteRule(ruleId: string): Promise<any> {
    const response = await this.client.delete(`/api/v1/config/rules/${ruleId}`);
    return response.data;
  }

  async exportConfig(params: { include_rules?: boolean }): Promise<any> {
    const response = await this.client.post('/api/v1/config/export', params);
    return response.data;
  }

  async importConfig(request: {
    config: Record<string, any>;
    rules: Record<string, any>;
    overwrite?: boolean;
  }): Promise<any> {
    const response = await this.client.post('/api/v1/config/import', request);
    return response.data;
  }

  async getConfigHealth(): Promise<HealthStatus> {
    const response = await this.client.get('/api/v1/config/health');
    return response.data;
  }

  async getConfigAuditLogs(params: {
    limit?: number;
    offset?: number;
  }): Promise<PaginatedResponse<any>> {
    const response = await this.client.get('/api/v1/config/audit-logs', { params });
    return response.data;
  }

  // Health check
  async getHealth(): Promise<{ status: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}

// Create singleton instance
export const apiClient = new ApiClient();

// Export types for convenience
export type {
  LoginRequest,
  LoginResponse,
  ScoreRequest,
  ScoringResult,
  BatchScoreRequest,
  AgentRunRequest,
  AgentResult,
  PipelineRunRequest,
  PipelineResult,
  ConfigUpdateRequest,
  RuleCreateRequest,
  HealthStatus,
  PaginatedResponse,
  Entity,
  Context,
};
