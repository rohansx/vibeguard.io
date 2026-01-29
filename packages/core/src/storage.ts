import Database from 'better-sqlite3';
import { Action, ActionQuery, ActionStatus, RiskLevel } from './types';
import { join } from 'path';
import { existsSync, mkdirSync } from 'fs';
import { homedir } from 'os';

/**
 * Storage layer for Vibeguard actions
 */
export class ActionStorage {
  private db: Database.Database;

  constructor(dbPath?: string) {
    const path = dbPath || this.getDefaultPath();
    this.ensureDirectory(path);
    this.db = new Database(path);
    this.initialize();
  }

  private getDefaultPath(): string {
    const configDir = join(homedir(), '.vibeguard');
    return join(configDir, 'actions.db');
  }

  private ensureDirectory(dbPath: string): void {
    const dir = dbPath.substring(0, dbPath.lastIndexOf('/'));
    if (dir && !existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  }

  private initialize(): void {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS actions (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        agent TEXT NOT NULL,
        type TEXT NOT NULL,
        description TEXT NOT NULL,
        details TEXT,
        risk TEXT NOT NULL,
        status TEXT NOT NULL,
        context TEXT,
        reversible INTEGER NOT NULL DEFAULT 0,
        undo_data TEXT,
        result TEXT,
        error TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_actions_agent ON actions(agent);
      CREATE INDEX IF NOT EXISTS idx_actions_type ON actions(type);
      CREATE INDEX IF NOT EXISTS idx_actions_risk ON actions(risk);
      CREATE INDEX IF NOT EXISTS idx_actions_status ON actions(status);
      CREATE INDEX IF NOT EXISTS idx_actions_timestamp ON actions(timestamp);
    `);
  }

  /**
   * Insert a new action
   */
  insert(action: Action): void {
    const stmt = this.db.prepare(`
      INSERT INTO actions (
        id, timestamp, agent, type, description, details,
        risk, status, context, reversible, undo_data, result, error
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    stmt.run(
      action.id,
      action.timestamp.toISOString(),
      action.agent,
      action.type,
      action.description,
      JSON.stringify(action.details),
      action.risk,
      action.status,
      JSON.stringify(action.context),
      action.reversible ? 1 : 0,
      action.undoData ? JSON.stringify(action.undoData) : null,
      action.result ? JSON.stringify(action.result) : null,
      action.error || null
    );
  }

  /**
   * Update an existing action
   */
  update(id: string, updates: Partial<Action>): void {
    const fields: string[] = [];
    const values: unknown[] = [];

    if (updates.status !== undefined) {
      fields.push('status = ?');
      values.push(updates.status);
    }
    if (updates.result !== undefined) {
      fields.push('result = ?');
      values.push(JSON.stringify(updates.result));
    }
    if (updates.error !== undefined) {
      fields.push('error = ?');
      values.push(updates.error);
    }

    if (fields.length === 0) return;

    values.push(id);
    const stmt = this.db.prepare(
      `UPDATE actions SET ${fields.join(', ')} WHERE id = ?`
    );
    stmt.run(...values);
  }

  /**
   * Get an action by ID
   */
  get(id: string): Action | null {
    const stmt = this.db.prepare('SELECT * FROM actions WHERE id = ?');
    const row = stmt.get(id) as Record<string, unknown> | undefined;
    return row ? this.rowToAction(row) : null;
  }

  /**
   * Query actions
   */
  query(options: ActionQuery = {}): Action[] {
    const conditions: string[] = [];
    const values: unknown[] = [];

    if (options.agent) {
      conditions.push('agent = ?');
      values.push(options.agent);
    }
    if (options.type) {
      conditions.push('type = ?');
      values.push(options.type);
    }
    if (options.risk) {
      conditions.push('risk = ?');
      values.push(options.risk);
    }
    if (options.status) {
      conditions.push('status = ?');
      values.push(options.status);
    }
    if (options.since) {
      conditions.push('timestamp >= ?');
      values.push(options.since.toISOString());
    }
    if (options.until) {
      conditions.push('timestamp <= ?');
      values.push(options.until.toISOString());
    }

    let sql = 'SELECT * FROM actions';
    if (conditions.length > 0) {
      sql += ' WHERE ' + conditions.join(' AND ');
    }
    sql += ' ORDER BY timestamp DESC';

    if (options.limit) {
      sql += ' LIMIT ?';
      values.push(options.limit);
    }
    if (options.offset) {
      sql += ' OFFSET ?';
      values.push(options.offset);
    }

    const stmt = this.db.prepare(sql);
    const rows = stmt.all(...values) as Record<string, unknown>[];
    return rows.map((row) => this.rowToAction(row));
  }

  /**
   * Get recent actions
   */
  recent(limit = 50): Action[] {
    return this.query({ limit });
  }

  /**
   * Get actions by agent
   */
  byAgent(agent: string, limit = 50): Action[] {
    return this.query({ agent, limit });
  }

  /**
   * Get actions by risk level
   */
  byRisk(risk: RiskLevel, limit = 50): Action[] {
    return this.query({ risk, limit });
  }

  /**
   * Get statistics
   */
  stats(): {
    total: number;
    byRisk: Record<RiskLevel, number>;
    byStatus: Record<ActionStatus, number>;
    byAgent: Record<string, number>;
  } {
    const total = (
      this.db.prepare('SELECT COUNT(*) as count FROM actions').get() as {
        count: number;
      }
    ).count;

    const byRisk = {} as Record<RiskLevel, number>;
    const riskRows = this.db
      .prepare('SELECT risk, COUNT(*) as count FROM actions GROUP BY risk')
      .all() as { risk: RiskLevel; count: number }[];
    for (const row of riskRows) {
      byRisk[row.risk] = row.count;
    }

    const byStatus = {} as Record<ActionStatus, number>;
    const statusRows = this.db
      .prepare('SELECT status, COUNT(*) as count FROM actions GROUP BY status')
      .all() as { status: ActionStatus; count: number }[];
    for (const row of statusRows) {
      byStatus[row.status] = row.count;
    }

    const byAgent = {} as Record<string, number>;
    const agentRows = this.db
      .prepare('SELECT agent, COUNT(*) as count FROM actions GROUP BY agent')
      .all() as { agent: string; count: number }[];
    for (const row of agentRows) {
      byAgent[row.agent] = row.count;
    }

    return { total, byRisk, byStatus, byAgent };
  }

  /**
   * Close the database connection
   */
  close(): void {
    this.db.close();
  }

  private rowToAction(row: Record<string, unknown>): Action {
    return {
      id: row.id as string,
      timestamp: new Date(row.timestamp as string),
      agent: row.agent as string,
      type: row.type as string,
      description: row.description as string,
      details: JSON.parse((row.details as string) || '{}'),
      risk: row.risk as RiskLevel,
      status: row.status as ActionStatus,
      context: JSON.parse((row.context as string) || '{}'),
      reversible: row.reversible === 1,
      undoData: row.undo_data ? JSON.parse(row.undo_data as string) : undefined,
      result: row.result ? JSON.parse(row.result as string) : undefined,
      error: row.error as string | undefined,
    };
  }
}
