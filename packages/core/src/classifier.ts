import { ActionType, RiskLevel, ActionInput } from './types';

/**
 * Default risk levels for action types
 */
const DEFAULT_RISK_MAP: Record<string, RiskLevel> = {
  // Low risk - read-only, no side effects
  [ActionType.FILE_READ]: RiskLevel.LOW,
  
  // Medium risk - reversible side effects
  [ActionType.FILE_WRITE]: RiskLevel.MEDIUM,
  [ActionType.FILE_COPY]: RiskLevel.MEDIUM,
  [ActionType.FILE_MOVE]: RiskLevel.MEDIUM,
  [ActionType.CONFIG_CHANGE]: RiskLevel.MEDIUM,
  
  // High risk - potentially dangerous
  [ActionType.FILE_DELETE]: RiskLevel.HIGH,
  [ActionType.SHELL_COMMAND]: RiskLevel.HIGH,
  [ActionType.CODE_EXECUTE]: RiskLevel.HIGH,
  [ActionType.API_CALL]: RiskLevel.HIGH,
  [ActionType.PERMISSION_CHANGE]: RiskLevel.HIGH,
  
  // Critical risk - irreversible, external effects
  [ActionType.EMAIL_SEND]: RiskLevel.CRITICAL,
  [ActionType.MESSAGE_SEND]: RiskLevel.CRITICAL,
  [ActionType.SOCIAL_POST]: RiskLevel.CRITICAL,
  [ActionType.PAYMENT]: RiskLevel.CRITICAL,
};

/**
 * Patterns that increase risk level
 */
const DANGEROUS_PATTERNS = [
  /rm\s+-rf/i,
  /sudo/i,
  /password/i,
  /secret/i,
  /api[_-]?key/i,
  /token/i,
  /credit[_-]?card/i,
  /\.env/i,
  /private[_-]?key/i,
];

/**
 * Patterns that indicate external communication
 */
const EXTERNAL_PATTERNS = [
  /@\w+\.\w+/,  // email addresses
  /https?:\/\//i,  // URLs
  /\+?\d{10,}/,  // phone numbers
];

/**
 * Classify the risk level of an action
 */
export function classifyRisk(action: ActionInput): RiskLevel {
  // If risk is explicitly set, use it
  if (action.risk) {
    return action.risk;
  }

  // Start with default risk for the action type
  let risk = DEFAULT_RISK_MAP[action.type] || RiskLevel.MEDIUM;

  // Check description and details for patterns
  const textToCheck = JSON.stringify({
    description: action.description,
    details: action.details,
  });

  // Check for dangerous patterns
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(textToCheck)) {
      risk = elevateRisk(risk);
      break;
    }
  }

  // Check for external communication
  for (const pattern of EXTERNAL_PATTERNS) {
    if (pattern.test(textToCheck)) {
      risk = elevateRisk(risk);
      break;
    }
  }

  return risk;
}

/**
 * Elevate risk level by one step
 */
function elevateRisk(current: RiskLevel): RiskLevel {
  switch (current) {
    case RiskLevel.LOW:
      return RiskLevel.MEDIUM;
    case RiskLevel.MEDIUM:
      return RiskLevel.HIGH;
    case RiskLevel.HIGH:
    case RiskLevel.CRITICAL:
      return RiskLevel.CRITICAL;
    default:
      return RiskLevel.HIGH;
  }
}

/**
 * Check if an action type is typically reversible
 */
export function isReversible(type: ActionType | string): boolean {
  const irreversibleTypes = [
    ActionType.EMAIL_SEND,
    ActionType.MESSAGE_SEND,
    ActionType.SOCIAL_POST,
    ActionType.PAYMENT,
  ];

  return !irreversibleTypes.includes(type as ActionType);
}

/**
 * Get a human-readable risk description
 */
export function getRiskDescription(risk: RiskLevel): string {
  switch (risk) {
    case RiskLevel.LOW:
      return 'Low risk - Read-only operation with no side effects';
    case RiskLevel.MEDIUM:
      return 'Medium risk - May modify data but typically reversible';
    case RiskLevel.HIGH:
      return 'High risk - Could cause significant changes or data loss';
    case RiskLevel.CRITICAL:
      return 'Critical risk - Irreversible action with external effects';
    default:
      return 'Unknown risk level';
  }
}
