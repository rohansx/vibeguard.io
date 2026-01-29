/**
 * Action types that can be captured
 */
export enum ActionType {
  // File System
  FILE_READ = 'file.read',
  FILE_WRITE = 'file.write',
  FILE_DELETE = 'file.delete',
  FILE_MOVE = 'file.move',
  FILE_COPY = 'file.copy',

  // Network
  HTTP_REQUEST = 'http.request',
  EMAIL_SEND = 'email.send',
  MESSAGE_SEND = 'message.send',

  // Code Execution
  SHELL_COMMAND = 'shell.command',
  CODE_EXECUTE = 'code.execute',

  // External Services
  API_CALL = 'api.call',
  PAYMENT = 'payment',
  SOCIAL_POST = 'social.post',

  // System
  CONFIG_CHANGE = 'config.change',
  PERMISSION_CHANGE = 'permission.change',

  // Generic
  CUSTOM = 'custom',
}

/**
 * Risk levels for actions
 */
export enum RiskLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

/**
 * Status of an action
 */
export enum ActionStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  EXECUTED = 'executed',
  BLOCKED = 'blocked',
  FAILED = 'failed',
  UNDONE = 'undone',
}

/**
 * Context about why an action was taken
 */
export interface ActionContext {
  sessionId?: string;
  conversationId?: string;
  userPrompt?: string;
  agentReasoning?: string;
  parentActionId?: string;
}

/**
 * An action captured by Vibeguard
 */
export interface Action {
  id: string;
  timestamp: Date;
  agent: string;
  type: ActionType | string;
  description: string;
  details: Record<string, unknown>;
  risk: RiskLevel;
  status: ActionStatus;
  context: ActionContext;
  reversible: boolean;
  undoData?: Record<string, unknown>;
  result?: unknown;
  error?: string;
}

/**
 * Input for creating a new action
 */
export interface ActionInput {
  agent: string;
  type: ActionType | string;
  description: string;
  details?: Record<string, unknown>;
  risk?: RiskLevel;
  context?: Partial<ActionContext>;
  reversible?: boolean;
  undoData?: Record<string, unknown>;
}

/**
 * Query options for listing actions
 */
export interface ActionQuery {
  agent?: string;
  type?: ActionType | string;
  risk?: RiskLevel;
  status?: ActionStatus;
  since?: Date;
  until?: Date;
  limit?: number;
  offset?: number;
}

/**
 * Result of an undo operation
 */
export interface UndoResult {
  success: boolean;
  actionId: string;
  message?: string;
  error?: string;
}

/**
 * Configuration for Vibeguard
 */
export interface VibeguardConfig {
  storagePath?: string;
  defaultAgent?: string;
  riskThreshold?: RiskLevel;
  autoClassify?: boolean;
}
