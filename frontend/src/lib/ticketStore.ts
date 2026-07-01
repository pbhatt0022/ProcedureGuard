import fs from 'fs';
import path from 'path';

const DATA_DIR = process.env.AIMS_DATA_DIR
  ? path.resolve(process.env.AIMS_DATA_DIR)
  : path.resolve(process.cwd(), '..', 'data');

const TICKETS_DB_PATH = path.join(DATA_DIR, 'tickets_db.json');
const INCIDENTS_DIR   = path.join(DATA_DIR, 'incidents');
const DIAGNOSES_DIR   = path.join(DATA_DIR, 'diagnoses');

export interface HistoryEntry { action: string; by: string; at: string; }
export interface Comment      { author: string; at: string; text: string; }

export interface Ticket {
  ticket_id: string;
  run_id: string;
  step_id: string;
  sequence_position: number;
  section: string;
  sop_step: string;
  verdict: string;
  timestamp: string;
  confidence: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
  severity_reason: string;
  incident_summary: string;
  recommended_action: string;
  status: string;
  assigned_to: string;
  created_at: string;
  comments: Comment[];
  history: HistoryEntry[];
  sla_window_started_at?: string;
  escalation_count?: number;
}

export type TicketsDb = Record<string, Ticket>;

export interface DiagnosisMember {
  ticket_id: string;
  role: 'root_cause' | 'consequence' | 'contributing';
  caused_by: string[];
  reason: string;
}

export interface DiagnosisGroup {
  label: string;
  members: DiagnosisMember[];
}

export interface Diagnosis {
  run_id: string;
  total_incidents: number;
  root_cause_count: number;
  group_count: number;
  diagnosis: string;
  groups: DiagnosisGroup[];
}

export function utcStamp(): string {
  return new Date().toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

function initFromIncidents(db: TicketsDb): TicketsDb {
  if (!fs.existsSync(INCIDENTS_DIR)) return db;
  for (const file of fs.readdirSync(INCIDENTS_DIR)) {
    if (!file.endsWith('_incidents.json')) continue;
    try {
      const data = JSON.parse(fs.readFileSync(path.join(INCIDENTS_DIR, file), 'utf-8'));
      for (const inc of data.incidents ?? []) {
        const key = `${inc.run_id}__${inc.ticket_id}`;
        if (!(key in db)) {
          db[key] = {
            ...inc,
            comments: inc.comments ?? [],
            history: inc.history ?? [
              { action: 'Ticket created by system', by: 'System', at: utcStamp() },
            ],
          };
        }
      }
    } catch { /* skip malformed */ }
  }
  return db;
}

export function loadTicketsDb(): TicketsDb {
  let db: TicketsDb = {};
  if (fs.existsSync(TICKETS_DB_PATH)) {
    try { db = JSON.parse(fs.readFileSync(TICKETS_DB_PATH, 'utf-8')); } catch {}
  }
  const before = Object.keys(db).length;
  db = initFromIncidents(db);
  if (Object.keys(db).length > before) saveTicketsDb(db);
  return db;
}

export function saveTicketsDb(db: TicketsDb): void {
  fs.mkdirSync(path.dirname(TICKETS_DB_PATH), { recursive: true });
  fs.writeFileSync(TICKETS_DB_PATH, JSON.stringify(db, null, 2), 'utf-8');
}

export function findTicketKey(db: TicketsDb, ticketId: string): string | undefined {
  return Object.keys(db).find(k => db[k].ticket_id === ticketId);
}

export function listDiagnoses(): Diagnosis[] {
  if (!fs.existsSync(DIAGNOSES_DIR)) return [];
  return fs.readdirSync(DIAGNOSES_DIR)
    .filter(f => f.endsWith('_grouped.json'))
    .flatMap(f => {
      try { return [JSON.parse(fs.readFileSync(path.join(DIAGNOSES_DIR, f), 'utf-8'))]; }
      catch { return []; }
    });
}
