import {
  RunData,
  DashboardContext,
  DashboardRow,
  RawVerdict,
  NormalizedSegment,
  AuditEvent,
  Verdict
} from './types';

const VERDICT_ORDER: Verdict[] = [
  'Deviation Detected',
  'Requires Inspection',
  'Unable to Verify',
  'Compliant',
];

const ATTENTION_PRIORITY: Record<string, number> = {
  'Deviation Detected': 0,
  'Requires Inspection': 1,
  'Unable to Verify': 2,
  'Compliant': 3,
};

export function compactText(value: any): string {
  return String(value || '').trim().replace(/\s+/g, ' ');
}

export function truncateText(value: any, limit: number = 160): string {
  const text = compactText(value);
  if (!text) return '-';
  if (text.length <= limit) return text;
  return text.slice(0, limit - 3).trim() + '...';
}

export function confidencePercent(value: any): number | null {
  if (value === null || value === undefined) return null;
  const num = Number(value);
  if (isNaN(num)) return null;
  return Math.round(num * 100);
}

export function formatConfidence(value: any): string {
  const pct = confidencePercent(value);
  return pct !== null ? `${pct}%` : '-';
}

export function formatTimestamp(start: any, end: any): string {
  try {
    const s = start !== null && start !== undefined && !isNaN(Number(start)) ? Number(start) : null;
    const e = end !== null && end !== undefined && !isNaN(Number(end)) ? Number(end) : null;

    if (s === null && e === null) {
      return 'No evidence window';
    }
    if (s !== null && e !== null) {
      return `${s.toFixed(1)}s to ${e.toFixed(1)}s`;
    }
    if (s !== null) {
      return `${s.toFixed(1)}s`;
    }
    if (e !== null) {
      return `${e.toFixed(1)}s`;
    }
    return 'No evidence window';
  } catch {
    return 'No evidence window';
  }
}

export function parseDatetime(value: any): Date | null {
  if (!value) return null;
  try {
    const d = new Date(String(value));
    return isNaN(d.getTime()) ? null : d;
  } catch {
    return null;
  }
}

export function formatDatetime(value: any): string {
  const parsed = parseDatetime(value);
  if (!parsed) return !value ? '-' : String(value);
  return parsed.toISOString().slice(0, 16).replace('T', ' ') + ' UTC';
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined) return '-';
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  return `${minutes}:${remainder.toString().padStart(2, '0')}`;
}

function videoFilename(videoUrl: string | null): string {
  if (!videoUrl) return '-';
  try {
    // Handle both POSIX and Windows separators (run video_url is an absolute Windows path).
    const parts = videoUrl.replace(/\\/g, '/').split('/');
    const last = parts[parts.length - 1];
    return last || '-';
  } catch {
    return String(videoUrl);
  }
}

function computeScore(results: any, summary: any): number | null {
  let score = results?.adherence_score;
  if (score === undefined || score === null) {
    score = summary?.adherence_score;
  }
  if (score === undefined || score === null) {
    const compliant = Number(summary?.compliant || 0);
    const deviation = Number(summary?.deviation || 0);
    if (compliant + deviation > 0) {
      score = compliant / (compliant + deviation);
    } else {
      score = null;
    }
  }
  return score;
}

export function reviewStateForRow(row: Partial<DashboardRow>): [string, 'success' | 'warning' | 'review' | 'neutral'] {
  const verdict = row.verdict;
  if (verdict === 'Deviation Detected') {
    return ['Review required', 'review'];
  }
  if (verdict === 'Requires Inspection') {
    return ['Manual inspection', 'warning'];
  }
  if (verdict === 'Unable to Verify') {
    return ['Coverage check', 'warning'];
  }
  if (row.sequence_ok === false || row.duration_ok === false) {
    return ['Check trace', 'warning'];
  }
  return ['Auto-cleared', 'success'];
}

export function findMatchingSegment(
  row: Partial<DashboardRow>,
  observationSegments: NormalizedSegment[]
): NormalizedSegment | null {
  const segmentId = row.evidence_segment_id;
  if (segmentId) {
    for (const segment of observationSegments) {
      if (segment.segment_id === segmentId) {
        return segment;
      }
    }
  }

  const start = row.evidence_start;
  const end = row.evidence_end;
  if (start === null || start === undefined || end === null || end === undefined) {
    return null;
  }

  for (const segment of observationSegments) {
    const segStart = segment.start;
    const segEnd = segment.end;
    if (segStart === null || segStart === undefined || segEnd === null || segEnd === undefined) {
      continue;
    }
    let overlaps = false;
    if (start !== null && end !== null) {
      overlaps = segStart <= end && segEnd >= start;
    } else if (start !== null) {
      overlaps = segStart <= start && start <= segEnd;
    } else {
      overlaps = segStart <= end && end <= segEnd;
    }
    if (overlaps) {
      return segment;
    }
  }
  return null;
}

export function buildAuditEvents(ctx: Partial<DashboardContext>): AuditEvent[] {
  const events: AuditEvent[] = [];
  const createdAtRaw = ctx.created_at_raw;

  if (ctx.created_at && ctx.created_at !== '-') {
    events.push({
      timestamp: ctx.created_at,
      sort_value: createdAtRaw ? String(createdAtRaw) : null,
      actor: 'System',
      tone: 'info',
      title: 'Verification record assembled',
      body: `Run ${ctx.run_id} linked SOP ${ctx.sop_document} to video ${ctx.video_name} and generated the report shell.`,
    });
  }

  if (ctx.duration_text && ctx.duration_text !== '-') {
    events.push({
      timestamp: ctx.created_at || '-',
      sort_value: createdAtRaw ? String(createdAtRaw) : null,
      actor: 'Vision analyzer',
      tone: 'info',
      title: 'Video evidence indexed',
      body: `Processed ${ctx.total_segments} segment(s) across ${ctx.duration_text} of footage using ${ctx.analyzer_id}.`,
    });
  }

  if (ctx.deviation && ctx.deviation > 0) {
    events.push({
      timestamp: ctx.created_at || '-',
      sort_value: createdAtRaw ? String(createdAtRaw) : null,
      actor: 'Reasoning engine',
      tone: 'critical',
      title: 'Deviation queue created',
      body: `${ctx.deviation} step(s) were marked Deviation Detected and should be reviewed before any release decision.`,
    });
  }

  if (ctx.requires_inspection && ctx.requires_inspection > 0) {
    events.push({
      timestamp: ctx.created_at || '-',
      sort_value: createdAtRaw ? String(createdAtRaw) : null,
      actor: 'Reasoning engine',
      tone: 'warning',
      title: 'Manual inspection items opened',
      body: `${ctx.requires_inspection} step(s) were intentionally routed to human inspection because video evidence was insufficient for a safe verdict.`,
    });
  }

  if (ctx.unable_to_verify && ctx.unable_to_verify > 0) {
    events.push({
      timestamp: ctx.created_at || '-',
      sort_value: createdAtRaw ? String(createdAtRaw) : null,
      actor: 'Reasoning engine',
      tone: 'warning',
      title: 'Coverage gaps recorded',
      body: `${ctx.unable_to_verify} step(s) were left as Unable to Verify rather than guessed from incomplete footage.`,
    });
  }

  const attentionRows = ctx.attention_rows || [];
  for (const row of attentionRows.slice(0, 6)) {
    events.push({
      timestamp: formatDatetime(row.created_at),
      sort_value: row.created_at ? String(row.created_at) : null,
      actor: 'Reasoning engine',
      tone: row.verdict === 'Deviation Detected' ? 'critical' : 'warning',
      title: `${row.step_id} marked ${row.verdict}`,
      body: `${truncateText(row.criterion, 140)} Evidence window: ${row.evidence_window}.`,
    });
  }

  if (!ctx.review_queue_count) {
    events.push({
      timestamp: ctx.created_at || '-',
      sort_value: createdAtRaw ? String(createdAtRaw) : null,
      actor: 'System',
      tone: 'success',
      title: 'Ready for archival review',
      body: 'No unresolved deviations or manual-review items remain in this report.',
    });
  }

  events.sort((a, b) => {
    if (a.sort_value === null && b.sort_value === null) return a.title.localeCompare(b.title);
    if (a.sort_value === null) return 1;
    if (b.sort_value === null) return -1;
    const cmp = a.sort_value.localeCompare(b.sort_value);
    if (cmp !== 0) return cmp;
    return a.title.localeCompare(b.title);
  });

  return events;
}

export function buildDashboardContext(results: RunData): DashboardContext {
  const summary = results.summary || {};
  const checklistItems = results.checklist?.items || [];
  const verdicts = results.verdicts || [];
  const sopSteps = results.sop_steps?.steps || [];
  const observations = results.observations || {};
  const rawSegments = observations.segments || [];

  const checklistByItem: Record<string, any> = {};
  for (const item of checklistItems) {
    if (item.item_id) {
      checklistByItem[item.item_id] = item;
    }
  }

  const sopByStep: Record<string, any> = {};
  for (const step of sopSteps) {
    if (step.step_id) {
      sopByStep[step.step_id] = step;
    }
  }

  const sourceRows: any[] = verdicts.length > 0 ? verdicts : checklistItems;
  const rows: DashboardRow[] = [];

  for (const entry of sourceRows) {
    const itemId = entry.item_id || '';
    const stepId = entry.step_id || '';
    const checklistItem = checklistByItem[itemId] || {};
    const sopStep = sopByStep[stepId] || {};

    const verdict = (entry.verdict || 'Pending') as Verdict;
    const confidence = entry.confidence !== undefined ? entry.confidence : null;
    const evidenceStart = entry.evidence_timestamp_start !== undefined ? entry.evidence_timestamp_start : null;
    const evidenceEnd = entry.evidence_timestamp_end !== undefined ? entry.evidence_timestamp_end : null;
    const evidenceSegmentId = entry.evidence_segment_id || '';
    const keyframePath = entry.keyframe_blob_path || '';

    const hasEvidence = !!(
      keyframePath ||
      evidenceSegmentId ||
      evidenceStart !== null ||
      evidenceEnd !== null
    );

    const flags: string[] = [];
    if (entry.sequence_ok === false) {
      flags.push('Out of order');
    }
    if (entry.duration_ok === false) {
      flags.push('Duration exception');
    }
    if (verdict === 'Requires Inspection') {
      flags.push('Inspection only');
    } else if (verdict === 'Unable to Verify') {
      flags.push('No visible confirmation');
    }

    const row: Partial<DashboardRow> = {
      item_id: itemId,
      step_id: stepId,
      sequence: Number(
        entry.sequence ??
        checklistItem.sequence ??
        sopStep.sequence ??
        999
      ),
      section: String(
        entry.sop_section ??
        checklistItem.sop_section ??
        sopStep.section ??
        'Unlabeled step'
      ),
      criterion: String(
        entry.criterion ??
        checklistItem.criterion ??
        sopStep.description ??
        'No criterion recorded.'
      ),
      check_type: String(
        entry.check_type ??
        checklistItem.check_type ??
        sopStep.check_type ??
        'presence'
      ),
      reasoning: String(entry.reasoning || 'No reasoning recorded.'),
      verdict,
      confidence,
      confidence_pct: confidencePercent(confidence),
      evidence_start: evidenceStart,
      evidence_end: evidenceEnd,
      evidence_window: formatTimestamp(evidenceStart, evidenceEnd),
      evidence_segment_id: evidenceSegmentId,
      keyframe_blob_path: keyframePath,
      sequence_ok: entry.sequence_ok ?? null,
      duration_ok: entry.duration_ok ?? null,
      created_at: String(entry.created_at || ''),
      has_evidence: hasEvidence,
      flags,
    };

    const [reviewState, reviewTone] = reviewStateForRow(row);
    row.review_state = reviewState;
    row.review_tone = reviewTone;

    rows.push(row as DashboardRow);
  }

  // Sort by sequence, then step_id
  rows.sort((a, b) => {
    if (a.sequence !== b.sequence) return a.sequence - b.sequence;
    return a.step_id.localeCompare(b.step_id);
  });

  const counts: Record<string, number> = {};
  for (const row of rows) {
    counts[row.verdict] = (counts[row.verdict] || 0) + 1;
  }

  const total = Number(summary.total ?? rows.length ?? checklistItems.length ?? 0);
  const compliant = Number(summary.compliant ?? counts['Compliant'] ?? 0);
  const deviation = Number(summary.deviation ?? counts['Deviation Detected'] ?? 0);
  const unable = Number(summary.unable_to_verify ?? counts['Unable to Verify'] ?? 0);
  const inspection = Number(summary.requires_inspection ?? counts['Requires Inspection'] ?? 0);

  const score = computeScore(results, summary);
  const scorePct = score !== null ? Math.round(score * 100) : null;
  const verifiableTotal = compliant + deviation;
  const abstentionTotal = unable + inspection;

  const evidenceRows = rows.filter(r => r.has_evidence);
  const confirmedRows = rows.filter(r => r.verdict === 'Compliant');
  const attentionRows = rows.filter(r => VERDICT_ORDER.slice(0, 3).includes(r.verdict));
  
  // Sort attention rows by ATTENTION_PRIORITY then sequence
  attentionRows.sort((a, b) => {
    const priA = ATTENTION_PRIORITY[a.verdict] ?? 99;
    const priB = ATTENTION_PRIORITY[b.verdict] ?? 99;
    if (priA !== priB) return priA - priB;
    return a.sequence - b.sequence;
  });

  const evidenceBounds: number[] = [];
  for (const r of evidenceRows) {
    if (r.evidence_start !== null) evidenceBounds.push(r.evidence_start);
    if (r.evidence_end !== null) evidenceBounds.push(r.evidence_end);
  }

  const confidenceValues: number[] = [];
  for (const r of rows) {
    if (r.confidence_pct !== null) confidenceValues.push(r.confidence_pct);
  }

  const observationSegments: NormalizedSegment[] = [];
  for (const segment of rawSegments) {
    const start = segment.start_time_seconds;
    const end = segment.end_time_seconds;
    observationSegments.push({
      segment_id: segment.segment_id || '',
      start,
      end,
      window: formatTimestamp(start, end),
      action: compactText(segment.action_observed || ''),
    });
  }

  const ends = observationSegments.map(s => s.end).filter(e => e !== null && e !== undefined);
  const duration = ends.length > 0 ? Math.max(...ends) : 0;

  // Compute median confidence
  let medianConfidence: number | null = null;
  if (confidenceValues.length > 0) {
    const sorted = [...confidenceValues].sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    medianConfidence = sorted.length % 2 !== 0 ? sorted[mid] : Math.round((sorted[mid - 1] + sorted[mid]) / 2);
  }

  let decisionTitle = '';
  let decisionBody = '';
  let decisionAction = '';
  let workspaceStatus = '';
  let workspaceTone: 'critical' | 'review' | 'clear' = 'clear';

  if (deviation > 0) {
    decisionTitle = 'Human review required before release';
    decisionBody = `${deviation} deviation finding(s) were raised against the SOP. Review the cited evidence and confirm disposition before release.`;
    decisionAction = 'Start with the deviation queue, then capture reviewer notes for any override.';
    workspaceStatus = 'Deviation review required';
    workspaceTone = 'critical';
  } else if (inspection > 0) {
    decisionTitle = 'Manual inspection queue open';
    decisionBody = `${inspection} step(s) were intentionally deferred to human inspection because the check is visual-detail limited or inspection only.`;
    decisionAction = 'Use the review queue as the formal inspection checklist before export.';
    workspaceStatus = 'Manual inspection required';
    workspaceTone = 'review';
  } else if (unable > 0) {
    decisionTitle = 'Coverage gaps need review';
    decisionBody = `${unable} step(s) could not be safely confirmed from available footage. The system abstained instead of guessing.`;
    decisionAction = 'Confirm whether additional footage is needed or accept the abstentions as documented.';
    workspaceStatus = 'Coverage review required';
    workspaceTone = 'review';
  } else if (score !== null && score >= 0.95) {
    decisionTitle = 'Ready for final QA review';
    decisionBody = 'All verifiable steps passed threshold and no unresolved exceptions remain.';
    decisionAction = 'Export the record once the reviewer confirms the evidence package.';
    workspaceStatus = 'Ready for export';
    workspaceTone = 'clear';
  } else {
    decisionTitle = 'Below release threshold';
    decisionBody = 'The adherence score is below the release threshold after counting only verifiable steps.';
    decisionAction = 'Investigate failed or missing steps before release.';
    workspaceStatus = 'Below threshold';
    workspaceTone = 'critical';
  }

  const createdAtRaw =
    observations.analyzed_at ||
    results.sop_steps?.extracted_at ||
    (rows.length > 0 ? rows[0].created_at : null);
  const createdAt = formatDatetime(createdAtRaw);

  const ctx: Partial<DashboardContext> = {
    run_id: results.run_id || '-',
    sop_document: results.sop_steps?.sop_document || '-',
    // Serve the clip through the streaming API route (the raw video_url is a local
    // file path the browser can't load). Falls back to any legacy video_file.
    video_file: observations.video_url
      ? `/api/runs/${results.run_id}/video`
      : (observations.video_file || ''),
    video_name: videoFilename(observations.video_url || observations.video_file),
    analyzer_id: observations.analyzer_id || 'procedureguard_compliance_v1',
    created_at: createdAt,
    created_at_raw: createdAtRaw ? String(createdAtRaw) : '',
    summary: summary as any,
    rows,
    evidence_rows: evidenceRows,
    confirmed_rows: confirmedRows,
    attention_rows: attentionRows,
    deviation_rows: rows.filter(r => r.verdict === 'Deviation Detected'),
    inspection_rows: rows.filter(r => r.verdict === 'Requires Inspection'),
    unable_rows: rows.filter(r => r.verdict === 'Unable to Verify'),
    compliant_rows: confirmedRows,
    observation_segments: observationSegments,
    total_segments: Number(observations.total_segments ?? observationSegments.length),
    duration,
    duration_text: formatDuration(duration),
    total,
    compliant,
    deviation,
    unable_to_verify: unable,
    requires_inspection: inspection,
    verifiable_total: verifiableTotal,
    abstention_total: abstentionTotal,
    review_queue_count: rows.filter(r => r.review_state !== 'Auto-cleared').length,
    evidence_count: evidenceRows.length,
    sequence_flags: rows.filter(r => r.sequence_ok === false).length,
    duration_flags: rows.filter(r => r.duration_ok === false).length,
    score,
    score_pct: scorePct,
    score_text: scorePct !== null ? `${scorePct}%` : '-',
    median_confidence: medianConfidence,
    evidence_window_start: evidenceBounds.length > 0 ? Math.min(...evidenceBounds) : null,
    evidence_window_end: evidenceBounds.length > 0 ? Math.max(...evidenceBounds) : null,
    decision_title: decisionTitle,
    decision_body: decisionBody,
    decision_action: decisionAction,
    workspace_status: workspaceStatus,
    workspace_tone: workspaceTone,
  };

  ctx.audit_events = buildAuditEvents(ctx);

  return ctx as DashboardContext;
}
