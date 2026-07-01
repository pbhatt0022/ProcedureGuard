'use client';

import React, { useState, useEffect, useCallback } from 'react';
import type { Ticket, Diagnosis } from '../../lib/ticketStore';
import { ESCALATION_PATH, SLA_POLICY } from '../../lib/slaPolicy';

// ── Constants ────────────────────────────────────────────────────────────────

const ROLES = ['Production Manager', 'QA Manager', 'Supervisor', 'QA Log'] as const;
type Role = typeof ROLES[number];

const ROLE_RANK: Record<string, number> = {
  'QA Log': 1, 'Supervisor': 2, 'QA Manager': 3, 'Production Manager': 4,
};


const SEV_STYLE: Record<string, { bg: string; text: string; dot: string }> = {
  critical: { bg: 'bg-pg-semantic-error-bg',   text: 'text-pg-semantic-error',   dot: 'bg-pg-semantic-error'   },
  high:     { bg: 'bg-orange-50',              text: 'text-orange-600',           dot: 'bg-orange-500'          },
  medium:   { bg: 'bg-yellow-50',              text: 'text-yellow-700',           dot: 'bg-yellow-500'          },
  low:      { bg: 'bg-pg-semantic-success-bg', text: 'text-pg-semantic-success',  dot: 'bg-pg-semantic-success' },
};

const STATUS_STYLE: Record<string, string> = {
  Open:          'text-pg-semantic-error font-bold',
  'In Review':   'text-orange-600 font-bold',
  Escalated:     'text-pg-semantic-review font-bold',
  'Needs Review':'text-blue-600 font-bold',
  'SLA Breached':'text-red-900 font-bold',
  Closed:        'text-pg-semantic-success font-bold',
};

type TabId = 'mine' | 'all' | 'review' | 'diagnoses' | 'history';
type TicketsDb = Record<string, Ticket>;

// ── SLA helper ───────────────────────────────────────────────────────────────

function slaStatus(ticket: Ticket): { label: string; level: 'ok' | 'due' | 'over' | 'breached' | 'closed' } {
  if (ticket.status === 'Closed')       return { label: '—',           level: 'closed'   };
  if (ticket.status === 'SLA Breached') return { label: 'SLA BREACHED', level: 'breached' };

  const policy = SLA_POLICY[ticket.severity] ?? SLA_POLICY.medium;
  const start  = new Date(ticket.sla_window_started_at ?? ticket.created_at);
  const ageMin = (Date.now() - start.getTime()) / 60_000;
  const rem    = policy.escalate - ageMin;

  const fmt = (m: number) => {
    const h = Math.floor(m / 60), mn = Math.round(m % 60);
    return h > 0 ? `${h}h ${mn}m` : `${mn}m`;
  };

  if (ageMin >= policy.escalate) return { label: 'OVERDUE',          level: 'over' };
  if (ageMin >= policy.remind)   return { label: `Due in ${fmt(rem)}`, level: 'due'  };
  return                                { label: `${fmt(rem)} left`,  level: 'ok'   };
}

// ── Small UI pieces ──────────────────────────────────────────────────────────

function SeverityBadge({ sev }: { sev: string }) {
  const s = SEV_STYLE[sev] ?? SEV_STYLE.low;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${s.bg} ${s.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {sev}
    </span>
  );
}

function SlaBadge({ ticket }: { ticket: Ticket }) {
  const { label, level } = slaStatus(ticket);
  if (level === 'closed') return null;
  const color = level === 'breached' ? 'text-red-900' : level === 'over' ? 'text-pg-semantic-error' : level === 'due' ? 'text-orange-500' : 'text-pg-ink-muted';
  return <span className={`text-[10px] font-semibold ${color}`}>{label}</span>;
}

function RoleBadge({ role }: { role: 'root_cause' | 'consequence' | 'contributing' }) {
  const map = {
    root_cause:   { label: 'ROOT CAUSE',  cls: 'bg-blue-800 text-white'   },
    consequence:  { label: 'CONSEQUENCE', cls: 'bg-purple-700 text-white'  },
    contributing: { label: 'CONTRIBUTING',cls: 'bg-teal-700 text-white'    },
  };
  const { label, cls } = map[role] ?? map.contributing;
  return <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${cls}`}>{label}</span>;
}

// ── Ticket card (in list) ────────────────────────────────────────────────────

function TicketCard({ dbKey, ticket, onSelect }: { dbKey: string; ticket: Ticket; onSelect: () => void }) {
  const isReview = ticket.verdict === 'Unable to Verify';
  return (
    <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md p-4 flex items-start justify-between gap-4 hover:bg-pg-surface-hover transition-colors">
      <div className="flex flex-col gap-1.5 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <SeverityBadge sev={ticket.severity} />
          {isReview && (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-blue-100 text-blue-700">❔ UNABLE TO VERIFY</span>
          )}
          <span className="text-xs font-mono font-semibold text-pg-ink">{ticket.ticket_id}</span>
          <span className="text-xs text-pg-ink-muted">· {ticket.run_id} · Step {ticket.sequence_position}</span>
        </div>
        <p className="text-xs text-pg-ink font-medium truncate">{ticket.sop_step}</p>
        <div className="flex items-center gap-3 text-[10px] text-pg-ink-muted flex-wrap">
          <span>🕐 {ticket.timestamp}</span>
          <span>Confidence: {ticket.confidence}%</span>
          <span>Assigned: <strong className="text-pg-ink">{ticket.assigned_to}</strong></span>
          <span className={STATUS_STYLE[ticket.status] ?? 'text-pg-ink-muted'}>{ticket.status}</span>
          <SlaBadge ticket={ticket} />
        </div>
      </div>
      <button
        onClick={onSelect}
        className="shrink-0 text-xs font-semibold text-pg-primary border border-pg-primary/30 rounded-pg-sm px-3 py-1.5 hover:bg-pg-primary-subtle transition-colors btn-tactile"
      >
        View
      </button>
    </div>
  );
}

// ── Ticket detail panel ──────────────────────────────────────────────────────

function TicketDetail({
  dbKey, ticket, currentRole, userName,
  diagnoses, allTickets,
  onBack, onRefresh,
}: {
  dbKey: string; ticket: Ticket; currentRole: Role; userName: string;
  diagnoses: Diagnosis[]; allTickets: TicketsDb;
  onBack: () => void; onRefresh: () => void;
}) {
  const [comment, setComment] = useState('');
  const [busy, setBusy] = useState(false);

  const isReview   = ticket.verdict === 'Unable to Verify';
  const canAct     = (ROLE_RANK[currentRole] ?? 0) >= (ROLE_RANK[ticket.assigned_to] ?? 0);
  const nextRole   = ESCALATION_PATH[ticket.assigned_to];

  // root-cause lookup
  const runDiag = diagnoses.find(d => d.run_id === ticket.run_id);
  const memberMeta = runDiag?.groups
    .flatMap(g => g.members.map(m => ({ ...m, group_label: g.label })))
    .find(m => m.ticket_id === ticket.ticket_id);

  async function doAction(action: string) {
    setBusy(true);
    await fetch(`/api/tickets/${ticket.ticket_id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, comment, by: userName }),
    });
    setComment('');
    setBusy(false);
    onRefresh();
  }

  return (
    <div className="flex flex-col gap-5">
      {/* Back */}
      <button onClick={onBack} className="flex items-center gap-1 text-xs text-pg-ink-muted hover:text-pg-ink w-fit">
        ← Back to list
      </button>

      {/* Header */}
      <div className="flex items-start gap-3 flex-wrap">
        <SeverityBadge sev={ticket.severity} />
        <div>
          <h2 className="text-base font-bold text-pg-ink">{ticket.ticket_id} — {ticket.sop_step}</h2>
          <p className="text-xs text-pg-ink-muted mt-0.5">
            Run: <strong>{ticket.run_id}</strong> · Step {ticket.sequence_position} ({ticket.step_id}) · {ticket.section}
          </p>
        </div>
      </div>

      {isReview && (
        <div className="p-3 bg-blue-50 border border-blue-200 rounded-pg-sm text-xs text-blue-800">
          ❔ <strong>Unable to Verify</strong> — Agent 2 could not confirm this step. The severity rating below reflects the <em>risk of leaving it unverified</em>, not a confirmed defect.
        </div>
      )}

      {/* Metrics row */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: isReview ? 'Risk' : 'Severity', value: ticket.severity.toUpperCase() },
          { label: 'Confidence',  value: `${ticket.confidence}%` },
          { label: 'Timestamp',   value: ticket.timestamp },
          { label: 'Status',      value: ticket.status },
          { label: 'SLA',         value: slaStatus(ticket).label },
        ].map(({ label, value }) => (
          <div key={label} className="bg-pg-surface-2 border border-pg-hairline rounded-pg-sm p-3 flex flex-col gap-1">
            <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wide">{label}</span>
            <span className="text-sm font-semibold text-pg-ink">{value}</span>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-2 text-xs text-pg-ink">
        <p><strong>Assigned to:</strong> {ticket.assigned_to}</p>
        <p><strong>{isReview ? 'Why this risk level' : `Why ${ticket.severity}`}:</strong> {ticket.severity_reason}</p>
        <p><strong>{isReview ? 'What could not be verified' : 'Summary'}:</strong> {ticket.incident_summary}</p>
        <p><strong>Recommended action:</strong> {ticket.recommended_action}</p>
      </div>

      {/* Root-cause analysis */}
      {memberMeta && (
        <div className="bg-pg-surface-2 border border-pg-hairline rounded-pg-md p-4 flex flex-col gap-2">
          <h3 className="text-xs font-bold text-pg-ink uppercase tracking-wide">🔍 Root-Cause Analysis</h3>
          <div className="flex items-center gap-2">
            <RoleBadge role={memberMeta.role} />
            <span className="text-xs text-pg-ink-muted italic">{memberMeta.group_label}</span>
          </div>
          <p className="text-xs text-pg-ink-muted">{memberMeta.reason}</p>
          {memberMeta.caused_by?.length > 0 && (
            <p className="text-xs text-pg-ink">
              <strong>Caused by:</strong> {memberMeta.caused_by.join(', ')}
            </p>
          )}
        </div>
      )}

      <hr className="border-pg-hairline" />

      {/* Comments */}
      <div className="flex flex-col gap-3">
        <h3 className="text-xs font-bold text-pg-ink uppercase tracking-wide">💬 Comments</h3>
        {ticket.comments.length === 0
          ? <p className="text-xs text-pg-ink-muted">No comments yet.</p>
          : ticket.comments.map((c, i) => (
            <div key={i} className="bg-pg-surface-2 border border-pg-hairline rounded-pg-sm p-3">
              <p className="text-[10px] font-bold text-pg-ink">{c.author} · {c.at}</p>
              <p className="text-xs text-pg-ink mt-1">{c.text}</p>
            </div>
          ))
        }
        {ticket.status !== 'Closed' && (
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Add a comment…"
            rows={3}
            className="text-xs border border-pg-hairline rounded-pg-sm p-2.5 bg-pg-canvas text-pg-ink resize-none outline-none focus:border-pg-primary transition-colors"
          />
        )}
      </div>

      <hr className="border-pg-hairline" />

      {/* Actions */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-bold text-pg-ink uppercase tracking-wide">⚙️ Actions</h3>

        {ticket.status === 'Closed' ? (
          <p className="text-xs text-pg-ink-muted">This ticket is closed.</p>
        ) : !canAct ? (
          <p className="text-xs text-orange-600">
            This ticket is assigned to <strong>{ticket.assigned_to}</strong>. Your role ({currentRole}) cannot act on it.
          </p>
        ) : isReview ? (
          <div className="flex gap-2 flex-wrap">
            <button
              disabled={busy}
              onClick={() => doAction('mark_compliant')}
              className="text-xs font-semibold px-4 py-2 rounded-pg-sm bg-pg-semantic-success text-white hover:opacity-90 disabled:opacity-50 btn-tactile"
            >
              ✅ Mark Compliant
            </button>
            <button
              disabled={busy}
              onClick={() => doAction('promote_incident')}
              className="text-xs font-semibold px-4 py-2 rounded-pg-sm bg-pg-semantic-review text-white hover:opacity-90 disabled:opacity-50 btn-tactile"
            >
              ⬆️ Promote to Incident
            </button>
          </div>
        ) : (
          <div className="flex gap-2 flex-wrap">
            {comment.trim() && (
              <button
                disabled={busy}
                onClick={() => doAction('comment')}
                className="text-xs font-semibold px-4 py-2 rounded-pg-sm bg-pg-surface-3 text-pg-ink border border-pg-hairline hover:bg-pg-surface-hover disabled:opacity-50 btn-tactile"
              >
                Post Comment
              </button>
            )}
            <button
              disabled={busy}
              onClick={() => doAction('close')}
              className="text-xs font-semibold px-4 py-2 rounded-pg-sm bg-pg-semantic-success text-white hover:opacity-90 disabled:opacity-50 btn-tactile"
            >
              ✅ Close Ticket
            </button>
            {nextRole && (
              <button
                disabled={busy}
                onClick={() => doAction('escalate')}
                className="text-xs font-semibold px-4 py-2 rounded-pg-sm bg-pg-semantic-review text-white hover:opacity-90 disabled:opacity-50 btn-tactile"
              >
                ⬆️ Escalate to {nextRole}
              </button>
            )}
          </div>
        )}
      </div>

      <hr className="border-pg-hairline" />

      {/* History */}
      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-bold text-pg-ink uppercase tracking-wide">📋 History</h3>
        {[...ticket.history].reverse().map((h, i) => (
          <p key={i} className="text-[10px] text-pg-ink-muted">
            <strong className="text-pg-ink">{h.at}</strong> — {h.action} <em>(by {h.by})</em>
          </p>
        ))}
      </div>
    </div>
  );
}

// ── Diagnoses tab ────────────────────────────────────────────────────────────

function DiagnosesPanel({ diagnoses, tickets }: { diagnoses: Diagnosis[]; tickets: TicketsDb }) {
  const [selRun, setSelRun] = useState(diagnoses[0]?.run_id ?? '');
  const data = diagnoses.find(d => d.run_id === selRun);

  if (diagnoses.length === 0) {
    return (
      <div className="p-6 text-center text-xs text-pg-ink-muted">
        No diagnoses found. Run <code className="font-mono bg-pg-surface-2 px-1 rounded">python -m aims.agents.root_cause data/incidents/&lt;RUN&gt;_incidents.json</code> to generate them.
      </div>
    );
  }

  const ORDER: Record<string, number> = { root_cause: 0, contributing: 1, consequence: 2 };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-3">
        <label className="text-xs font-semibold text-pg-ink-muted">Run:</label>
        <select
          value={selRun}
          onChange={e => setSelRun(e.target.value)}
          className="text-xs border border-pg-hairline rounded-pg-sm px-2 py-1.5 bg-pg-canvas text-pg-ink outline-none focus:border-pg-primary"
        >
          {diagnoses.map(d => <option key={d.run_id} value={d.run_id}>{d.run_id}</option>)}
        </select>
      </div>

      {data && (
        <>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Total Incidents', value: data.total_incidents },
              { label: 'Root Causes',     value: data.root_cause_count },
              { label: 'Groups',          value: data.group_count },
            ].map(({ label, value }) => (
              <div key={label} className="bg-pg-surface-2 border border-pg-hairline rounded-pg-sm p-3">
                <p className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wide">{label}</p>
                <p className="text-xl font-extrabold text-pg-ink font-display">{value}</p>
              </div>
            ))}
          </div>

          <div className="p-3 bg-pg-primary-subtle/30 border border-pg-primary-border-subtle/40 rounded-pg-sm text-xs text-pg-ink">
            <strong>Diagnosis:</strong> {data.diagnosis}
          </div>

          <div className="flex flex-col gap-3">
            {data.groups.map((g, gi) => (
              <div key={gi} className="bg-pg-canvas border border-pg-hairline rounded-pg-md p-4 flex flex-col gap-2">
                <p className="text-xs font-bold text-pg-ink">Group {gi + 1}: {g.label}</p>
                {[...g.members]
                  .sort((a, b) => (ORDER[a.role] ?? 9) - (ORDER[b.role] ?? 9))
                  .map((m, mi) => {
                    const tk = Object.values(tickets).find(t => t.ticket_id === m.ticket_id);
                    return (
                      <div key={mi} className="flex items-start gap-2">
                        {tk && <SeverityBadge sev={tk.severity} />}
                        <RoleBadge role={m.role} />
                        <div className="flex flex-col gap-0.5 min-w-0">
                          <span className="text-xs font-mono font-semibold text-pg-ink">{m.ticket_id}</span>
                          {m.caused_by?.length > 0 && (
                            <span className="text-[10px] text-pg-ink-muted">⟵ caused by {m.caused_by.join(', ')}</span>
                          )}
                          <span className="text-[10px] text-pg-ink-muted">↳ {m.reason}</span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function IncidentsPage() {
  const [tickets,   setTickets]   = useState<TicketsDb>({});
  const [diagnoses, setDiagnoses] = useState<Diagnosis[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [activeTab, setActiveTab] = useState<TabId>('mine');
  const [selected,  setSelected]  = useState<string | null>(null);
  const [currentRole, setCurrentRole] = useState<Role>('QA Manager');

  const userName = currentRole; // display name = role for this demo

  const refresh = useCallback(() => {
    Promise.all([
      fetch('/api/tickets').then(r => r.json()),
      fetch('/api/diagnoses').then(r => r.json()),
    ]).then(([t, d]: [TicketsDb, Diagnosis[]]) => {
      setTickets(t);
      setDiagnoses(d);
      setLoading(false);
      // Keep selected ticket in sync after a mutation
      if (selected) {
        const key = Object.keys(t).find(k => t[k].ticket_id === selected.split('__')[1] || k === selected);
        if (!key) setSelected(null);
      }
    });
  }, [selected]);

  useEffect(() => { refresh(); }, []);

  const entries = Object.entries(tickets);
  const isReview  = (t: Ticket) => t.verdict === 'Unable to Verify';
  const isOpen    = (t: Ticket) => t.status !== 'Closed';

  const reviewOpen  = entries.filter(([, t]) => isReview(t) && t.status === 'Needs Review');
  const incidents   = entries.filter(([, t]) => !(isReview(t) && t.status === 'Needs Review'));
  const mineOpen    = incidents.filter(([, t]) => t.assigned_to === currentRole && isOpen(t));
  const allOpen     = incidents.filter(([, t]) => isOpen(t));
  const history     = entries.filter(([, t]) => t.status === 'Closed');

  const TABS: { id: TabId; label: string; count?: number }[] = [
    { id: 'mine',      label: 'My Tickets',  count: mineOpen.length    },
    { id: 'all',       label: 'All Tickets', count: allOpen.length     },
    { id: 'review',    label: 'Needs Review',count: reviewOpen.length  },
    { id: 'diagnoses', label: 'Diagnoses'                              },
    { id: 'history',   label: 'History',     count: history.length     },
  ];

  // ── Render ticket list for a given entries slice ──
  const renderList = (slice: [string, Ticket][]) => {
    if (slice.length === 0) {
      return <p className="text-xs text-pg-ink-muted py-6 text-center">No tickets in this view.</p>;
    }
    return (
      <div className="flex flex-col gap-2">
        {slice.map(([key, ticket]) => (
          <TicketCard
            key={key}
            dbKey={key}
            ticket={ticket}
            onSelect={() => setSelected(key)}
          />
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="py-8 px-8 max-w-5xl mx-auto w-full animate-pulse flex flex-col gap-4">
        {[1, 2, 3].map(i => (
          <div key={i} className="h-20 bg-pg-surface-3 rounded-pg-md border border-pg-hairline" />
        ))}
      </div>
    );
  }

  // ── Selected ticket: find the full (refreshed) ticket ──
  const selectedTicket = selected ? tickets[selected] : null;

  return (
    <div className="py-8 px-8 flex flex-col gap-6 max-w-5xl mx-auto w-full">

      {/* Page header */}
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-pg-ink">Incident Management</h1>
          <p className="text-xs text-pg-ink-muted mt-1">
            Agent 3 classifications · root-cause diagnoses · role-based triage
          </p>
        </div>

        {/* Role selector */}
        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-pg-ink-muted">Viewing as:</label>
          <select
            value={currentRole}
            onChange={e => { setCurrentRole(e.target.value as Role); setSelected(null); }}
            className="text-xs border border-pg-hairline rounded-pg-sm px-2.5 py-1.5 bg-pg-canvas text-pg-ink outline-none focus:border-pg-primary"
          >
            {ROLES.map(r => <option key={r} value={r}>{r}</option>)}
          </select>
        </div>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Open Tickets',    value: allOpen.length  },
          { label: 'Assigned to Me',  value: mineOpen.length },
          { label: 'Needs Review',    value: reviewOpen.length },
        ].map(({ label, value }) => (
          <div key={label} className="p-4 bg-pg-surface-1 border border-pg-hairline rounded-pg-md shadow-pg-subtle flex flex-col gap-1">
            <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">{label}</span>
            <span className="text-3xl font-extrabold text-pg-ink font-display">{value}</span>
          </div>
        ))}
      </div>

      {/* If a ticket is selected, show detail and return early */}
      {selected && selectedTicket ? (
        <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md p-6 shadow-pg-subtle">
          <TicketDetail
            dbKey={selected}
            ticket={selectedTicket}
            currentRole={currentRole}
            userName={userName}
            diagnoses={diagnoses}
            allTickets={tickets}
            onBack={() => setSelected(null)}
            onRefresh={refresh}
          />
        </div>
      ) : (
        <>
          {/* Tabs */}
          <div className="border-b border-pg-hairline flex gap-0">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-pg-primary text-pg-primary'
                    : 'border-transparent text-pg-ink-muted hover:text-pg-ink'
                }`}
              >
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span className={`ml-1.5 text-[10px] font-bold px-1.5 py-0.5 rounded-full ${
                    tab.id === 'review'
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-pg-surface-3 text-pg-ink-muted'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div>
            {activeTab === 'mine'      && renderList(mineOpen)}
            {activeTab === 'all'       && renderList(allOpen)}
            {activeTab === 'review'    && (
              <div className="flex flex-col gap-4">
                <p className="text-xs text-pg-ink-muted">
                  Agent 3 rated these unverifiable steps as medium-or-higher risk. Decide: confirm compliant or promote to incident.
                </p>
                {renderList(reviewOpen)}
              </div>
            )}
            {activeTab === 'diagnoses' && (
              <DiagnosesPanel diagnoses={diagnoses} tickets={tickets} />
            )}
            {activeTab === 'history'   && renderList(history)}
          </div>
        </>
      )}
    </div>
  );
}
