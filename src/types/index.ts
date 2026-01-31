// API Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_info: UserInfo;
}

export interface UserInfo {
  user_id: string;
  username: string;
  email: string;
  role: UserRole;
  permissions: Permission[];
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export type UserRole = 'admin' | 'analyst' | 'viewer' | 'api_client';

export type Permission = 
  | 'read'
  | 'write'
  | 'delete'
  | 'manage_users'
  | 'manage_config'
  | 'view_audit_logs'
  | 'manage_rules'
  | 'run_agents'
  | 'run_pipelines'
  | 'manage_pipelines';

// Entity and Signal Types
export type EntityType = 
  | 'host'
  | 'domain'
  | 'ip'
  | 'user'
  | 'service'
  | 'application'
  | 'network'
  | 'database';

export type SignalType = 
  | 'vulnerability'
  | 'port'
  | 'service'
  | 'dns'
  | 'ssl_certificate'
  | 'configuration'
  | 'activity'
  | 'authentication'
  | 'dependency'
  | 'subdomain'
  | 'whois';

export type SeverityLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface Entity {
  id: string;
  entity_type: EntityType;
  name: string;
  description?: string;
  properties: Record<string, any>;
}

export interface Signal {
  id: string;
  source: string;
  signal_type: SignalType;
  severity: SeverityLevel;
  description: string;
  timestamp?: string;
  entity_id?: string;
  properties: Record<string, any>;
}

export interface Context {
  entity: Entity;
  signals: Signal[];
}

// Scoring Types
export interface ScoreRequest {
  context: Context;
  engines: string[];
  include_recommendations?: boolean;
}

export interface ScoringResult {
  entity_id: string;
  entity_type: EntityType;
  engine_name: string;
  score: number;
  severity: SeverityLevel;
  factors: Record<string, any>;
  recommendations?: string[];
  timestamp: string;
}

export interface BatchScoreRequest {
  contexts: Context[];
  engines: string[];
  parallel?: boolean;
}

// Agent Types
export interface AgentRunRequest {
  agent_name: string;
  context: Context;
  scoring_result?: Record<string, any>;
  timeout_seconds?: number;
}

export interface AgentResult {
  agent_name: string;
  success: boolean;
  output?: Record<string, any>;
  error?: string;
  duration_ms: number;
  timestamp: string;
}

export interface PipelineRunRequest {
  pipeline_name?: string;
  agents?: string[];
  context: Context;
  scoring_result?: Record<string, any>;
  parallel?: boolean;
  timeout_seconds?: number;
}

export interface PipelineResult {
  pipeline_name: string;
  results: Record<string, AgentResult>;
  success_count: number;
  total_count: number;
  duration_ms: number;
  timestamp: string;
}

// Configuration Types
export interface ConfigUpdateRequest {
  config_key: string;
  value: any;
  description?: string;
}

export interface RuleCreateRequest {
  rule_id: string;
  rule_type: 'risk' | 'exposure' | 'drift';
  name: string;
  description?: string;
  condition: Record<string, any>;
  action: Record<string, any>;
  priority?: number;
  enabled?: boolean;
}

// UI State Types
export interface AppState {
  auth: AuthState;
  entities: EntityState;
  scoring: ScoringState;
  agents: AgentState;
  config: ConfigState;
  ui: UIState;
}

export interface AuthState {
  isAuthenticated: boolean;
  user: UserInfo | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface EntityState {
  entities: Entity[];
  selectedEntity: Entity | null;
  signals: Signal[];
  isLoading: boolean;
  error: string | null;
}

export interface ScoringState {
  results: ScoringResult[];
  selectedResults: ScoringResult[];
  engines: Record<string, any>;
  isLoading: boolean;
  error: string | null;
}

export interface AgentState {
  agents: Record<string, any>;
  pipelines: Record<string, any>;
  results: Record<string, AgentResult>;
  selectedPipeline: string | null;
  isLoading: boolean;
  error: string | null;
}

export interface ConfigState {
  config: Record<string, any>;
  rules: Record<string, any>;
  isLoading: boolean;
  error: string | null;
}

export interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark';
  notifications: Notification[];
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: string;
  autoClose?: boolean;
}

// Chart and Visualization Types
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
}

export interface GraphNode {
  id: string;
  type: EntityType;
  label: string;
  data: {
    entity: Entity;
    score?: number;
    severity?: SeverityLevel;
  };
  position?: { x: number; y: number };
  style?: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  data?: Record<string, any>;
  style?: Record<string, any>;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// Filter and Search Types
export interface EntityFilter {
  entity_types?: EntityType[];
  severity_levels?: SeverityLevel[];
  score_range?: [number, number];
  date_range?: [string, string];
  search_query?: string;
}

export interface PaginationParams {
  limit: number;
  offset: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status_code: number;
  timestamp: string;
}

export interface HealthStatus {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  features?: Record<string, any>;
  statistics?: Record<string, any>;
}
