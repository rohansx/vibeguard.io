/**
 * Basic example of using Vibeguard SDK
 */
import { createSDK, ActionType, RiskLevel } from '@vibeguard/sdk';

// Create SDK instance
const guard = createSDK({
  agent: 'example-agent',
  riskThreshold: RiskLevel.HIGH,
  gatePrompt: async (action) => {
    console.log('\n🛡️  VIBEGUARD - Approval Required');
    console.log('────────────────────────────────');
    console.log(`Action: ${action.description}`);
    console.log(`Risk: ${action.risk.toUpperCase()}`);
    console.log(`Type: ${action.type}`);
    console.log('────────────────────────────────\n');
    
    // In a real app, prompt the user
    // For demo, auto-approve
    return true;
  },
  onAction: (action) => {
    console.log(`📝 Logged: ${action.description} [${action.risk}]`);
  },
});

// Example: Reading a file (low risk, auto-approved)
async function readFile(path: string): Promise<string> {
  const result = await guard.guard({
    type: ActionType.FILE_READ,
    description: `Read file: ${path}`,
    execute: async () => {
      // Simulate file read
      return `Contents of ${path}`;
    },
  });

  if (result.blocked) {
    throw new Error('Action was blocked');
  }

  return result.result!;
}

// Example: Sending an email (critical risk, requires approval)
async function sendEmail(to: string, subject: string): Promise<boolean> {
  const result = await guard.guard({
    type: ActionType.EMAIL_SEND,
    description: `Send email to ${to}`,
    details: { to, subject },
    risk: RiskLevel.CRITICAL,
    execute: async () => {
      // Simulate email send
      console.log(`📧 Email sent to ${to}: "${subject}"`);
      return true;
    },
  });

  return !result.blocked && result.result === true;
}

// Example: Wrapping an existing function
const originalDelete = (path: string) => {
  console.log(`🗑️  Deleted: ${path}`);
  return true;
};

const safeDelete = guard.wrap(originalDelete, {
  type: ActionType.FILE_DELETE,
  description: 'Delete file',
  risk: RiskLevel.HIGH,
});

// Run examples
async function main() {
  console.log('🚀 Vibeguard Basic Example\n');

  // Low risk - auto approved
  const content = await readFile('/docs/readme.md');
  console.log(`Read result: ${content}\n`);

  // Critical risk - will trigger approval prompt
  await sendEmail('john@example.com', 'Hello from Vibeguard');
  console.log('');

  // High risk - wrapped function
  await safeDelete('/tmp/old-file.txt');
  console.log('');

  // Show stats
  const stats = guard.stats();
  console.log('📊 Statistics:', stats);

  // Cleanup
  guard.close();
}

main().catch(console.error);
