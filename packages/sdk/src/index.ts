import {
  createVibeguard,
  Vibeguard,
  Action,
  ActionInput,
  ActionType,
  RiskLevel,
  ActionStatus,
  VibeguardConfig,
} from '@vibeguard/core';

export { ActionType, RiskLevel, ActionStatus } from '@vibeguard/core';

/**
 * Options for guarding an action
 */
export interface GuardOptions<T> {
  type: ActionType | string;
  description: string;
  execute: () => T | Promise<T>;
  details?: Record<string, unknown>;
  risk?: RiskLevel;
  context?: {
    sessionId?: string;
    userPrompt?: string;
    agentReasoning?: string;
  };
  reversible?: boolean;
  undoFn?: () => void | Promise<void>;
}

/**
 * Result of a guarded action
 */
export interface GuardResult<T> {
  action: Action;
  result?: T;
  blocked: boolean;
  error?: string;
}

/**
 * SDK configuration
 */
export interface SDKConfig extends VibeguardConfig {
  agent: string;
  gatePrompt?: (action: Action) => Promise<boolean>;
  onAction?: (action: Action) => void;
}

/**
 * Vibeguard SDK for AI agents
 */
export class VibeguardSDK {
  private core: Vibeguard;
  private config: SDKConfig;

  constructor(config: SDKConfig) {
    this.config = config;
    this.core = createVibeguard({
      storagePath: config.storagePath,
      defaultAgent: config.agent,
      riskThreshold: config.riskThreshold,
      autoClassify: config.autoClassify ?? true,
    });
  }

  /**
   * Guard and execute an action
   */
  async guard<T>(options: GuardOptions<T>): Promise<GuardResult<T>> {
    // Capture the action
    const action = this.core.capture({
      agent: this.config.agent,
      type: options.type,
      description: options.description,
      details: options.details,
      risk: options.risk,
      context: options.context,
      reversible: options.reversible ?? !!options.undoFn,
      undoData: options.undoFn ? { hasFn: true } : undefined,
    });

    // Notify listener
    if (this.config.onAction) {
      this.config.onAction(action);
    }

    // Check if gating is needed
    if (this.core.shouldGate(action)) {
      let approved = true;

      if (this.config.gatePrompt) {
        approved = await this.config.gatePrompt(action);
      }

      if (!approved) {
        this.core.block(action.id);
        return {
          action: { ...action, status: ActionStatus.BLOCKED },
          blocked: true,
        };
      }

      this.core.approve(action.id);
    }

    // Execute the action
    try {
      const result = await options.execute();
      this.core.complete(action.id, result);
      return {
        action: { ...action, status: ActionStatus.EXECUTED, result },
        result,
        blocked: false,
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      this.core.fail(action.id, errorMsg);
      return {
        action: { ...action, status: ActionStatus.FAILED, error: errorMsg },
        blocked: false,
        error: errorMsg,
      };
    }
  }

  /**
   * Capture an action without execution
   */
  capture(input: Omit<ActionInput, 'agent'>): Action {
    return this.core.capture({
      ...input,
      agent: this.config.agent,
    });
  }

  /**
   * Wrap a function with Vibeguard
   */
  wrap<TArgs extends unknown[], TResult>(
    fn: (...args: TArgs) => TResult | Promise<TResult>,
    options: Omit<GuardOptions<TResult>, 'execute'>
  ): (...args: TArgs) => Promise<GuardResult<TResult>> {
    return async (...args: TArgs) => {
      return this.guard({
        ...options,
        execute: () => fn(...args),
        details: { ...options.details, args },
      });
    };
  }

  /**
   * Get recent actions
   */
  recent(limit = 50): Action[] {
    return this.core.recent(limit);
  }

  /**
   * Get statistics
   */
  stats() {
    return this.core.stats();
  }

  /**
   * Undo an action
   */
  async undo(actionId: string) {
    return this.core.undo(actionId);
  }

  /**
   * Close connections
   */
  close(): void {
    this.core.close();
  }
}

/**
 * Create a new VibeguardSDK instance
 */
export function createSDK(config: SDKConfig): VibeguardSDK {
  return new VibeguardSDK(config);
}

// Default instance for quick usage
let defaultInstance: VibeguardSDK | null = null;

/**
 * Initialize the default SDK instance
 */
export function init(config: SDKConfig): VibeguardSDK {
  defaultInstance = new VibeguardSDK(config);
  return defaultInstance;
}

/**
 * Get the default SDK instance
 */
export function getSDK(): VibeguardSDK {
  if (!defaultInstance) {
    throw new Error('Vibeguard SDK not initialized. Call init() first.');
  }
  return defaultInstance;
}

// Convenience export
export const vibeguard = {
  init,
  getSDK,
  createSDK,
};
