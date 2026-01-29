// Core exports
export { Vibeguard, createVibeguard } from './vibeguard';
export { ActionStorage } from './storage';
export { classifyRisk, isReversible, getRiskDescription } from './classifier';

// Type exports
export {
  ActionType,
  RiskLevel,
  ActionStatus,
  Action,
  ActionInput,
  ActionQuery,
  ActionContext,
  UndoResult,
  VibeguardConfig,
} from './types';
