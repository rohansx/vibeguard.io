import { nanoid } from 'nanoid';
import { ActionStorage } from './storage';
import { classifyRisk, isReversible } from './classifier';
import {
  Action,
  ActionInput,
  ActionQuery,
  ActionStatus,
  RiskLevel,
  UndoResult,
  VibeguardConfig,
} from './types';

/**
 * Main Vibeguard class for capturing and managing actions
 */
export class Vibeguard {
  private storage: ActionStorage;
  private config: VibeguardConfig;

  constructor(config: VibeguardConfig = {}) {
    this.config = {
      autoClassify: true,
      ...config,
    };
    this.storage = new ActionStorage(config.storagePath);
  }

  /**
   * Capture a new action
   */
  capture(input: ActionInput): Action {
    const id = nanoid();
    const timestamp = new Date();

    // Auto-classify risk if not provided
    const risk = this.config.autoClassify
      ? classifyRisk(input)
      : input.risk || RiskLevel.MEDIUM;

    // Determine if reversible
    const reversible = input.reversible ?? isReversible(input.type);

    const action: Action = {
      id,
      timestamp,
      agent: input.agent || this.config.defaultAgent || 'unknown',
      type: input.type,
      description: input.description,
      details: input.details || {},
      risk,
      status: ActionStatus.PENDING,
      context: input.context || {},
      reversible,
      undoData: input.undoData,
    };

    this.storage.insert(action);
    return action;
  }

  /**
   * Mark an action as approved
   */
  approve(actionId: string): Action | null {
    const action = this.storage.get(actionId);
    if (!action) return null;

    this.storage.update(actionId, { status: ActionStatus.APPROVED });
    return { ...action, status: ActionStatus.APPROVED };
  }

  /**
   * Mark an action as blocked
   */
  block(actionId: string): Action | null {
    const action = this.storage.get(actionId);
    if (!action) return null;

    this.storage.update(actionId, { status: ActionStatus.BLOCKED });
    return { ...action, status: ActionStatus.BLOCKED };
  }

  /**
   * Mark an action as executed with optional result
   */
  complete(actionId: string, result?: unknown): Action | null {
    const action = this.storage.get(actionId);
    if (!action) return null;

    this.storage.update(actionId, {
      status: ActionStatus.EXECUTED,
      result,
    });
    return { ...action, status: ActionStatus.EXECUTED, result };
  }

  /**
   * Mark an action as failed with error
   */
  fail(actionId: string, error: string): Action | null {
    const action = this.storage.get(actionId);
    if (!action) return null;

    this.storage.update(actionId, {
      status: ActionStatus.FAILED,
      error,
    });
    return { ...action, status: ActionStatus.FAILED, error };
  }

  /**
   * Attempt to undo an action
   */
  async undo(actionId: string): Promise<UndoResult> {
    const action = this.storage.get(actionId);

    if (!action) {
      return {
        success: false,
        actionId,
        error: 'Action not found',
      };
    }

    if (!action.reversible) {
      return {
        success: false,
        actionId,
        error: 'Action is not reversible',
      };
    }

    if (action.status === ActionStatus.UNDONE) {
      return {
        success: false,
        actionId,
        error: 'Action has already been undone',
      };
    }

    // Mark as undone
    this.storage.update(actionId, { status: ActionStatus.UNDONE });

    return {
      success: true,
      actionId,
      message: 'Action marked as undone. Actual undo logic depends on action type.',
    };
  }

  /**
   * Get an action by ID
   */
  get(actionId: string): Action | null {
    return this.storage.get(actionId);
  }

  /**
   * Query actions
   */
  query(options?: ActionQuery): Action[] {
    return this.storage.query(options);
  }

  /**
   * Get recent actions
   */
  recent(limit = 50): Action[] {
    return this.storage.recent(limit);
  }

  /**
   * Get actions by agent
   */
  byAgent(agent: string, limit = 50): Action[] {
    return this.storage.byAgent(agent, limit);
  }

  /**
   * Get actions by risk level
   */
  byRisk(risk: RiskLevel, limit = 50): Action[] {
    return this.storage.byRisk(risk, limit);
  }

  /**
   * Get statistics
   */
  stats() {
    return this.storage.stats();
  }

  /**
   * Check if an action should be gated based on risk threshold
   */
  shouldGate(action: Action): boolean {
    if (!this.config.riskThreshold) return false;

    const riskOrder = [
      RiskLevel.LOW,
      RiskLevel.MEDIUM,
      RiskLevel.HIGH,
      RiskLevel.CRITICAL,
    ];

    const actionRiskIndex = riskOrder.indexOf(action.risk);
    const thresholdIndex = riskOrder.indexOf(this.config.riskThreshold);

    return actionRiskIndex >= thresholdIndex;
  }

  /**
   * Close the storage connection
   */
  close(): void {
    this.storage.close();
  }
}

/**
 * Create a new Vibeguard instance
 */
export function createVibeguard(config?: VibeguardConfig): Vibeguard {
  return new Vibeguard(config);
}
