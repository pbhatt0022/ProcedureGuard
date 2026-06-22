export type Verdict = 'Compliant' | 'Deviation Detected' | 'Requires Inspection' | 'Unable to Verify' | 'Pending';

export interface ReviewOverride {
  verdict: Verdict;
  notes: string;
  reviewer: string;
  timestamp: string;
  status: 'Confirmed compliant' | 'Confirmed deviation' | 'Marked unable to verify' | 'Escalated' | 'In review';
}


export interface SopStep {
  step_id: string;
  sequence: number;
  description: string;
  check_type: string;
  expected_duration_seconds: number | null;
  section: string;
  visual_references: any[];
}

export interface ChecklistItem {
  item_id: string;
  step_id: string;
  criterion: string;
  check_type: string;
  sequence?: number;
  sop_section?: string;
}

export interface ObservationSegment {
  segment_id: string;
  start_time_seconds: number;
  end_time_seconds: number;
  action_observed: string;
}

export interface RawVerdict {
  item_id: string;
  step_id: string;
  sequence?: number;
  sop_section?: string;
  criterion?: string;
  verdict: Verdict;
  confidence: number | null;
  evidence_segment_id: string | null;
  evidence_timestamp_start: number | null;
  evidence_timestamp_end: number | null;
  keyframe_blob_path: string | null;
  reasoning: string | null;
  sequence_ok: boolean | null;
  duration_ok: boolean | null;
  not_observed?: boolean;
  created_at?: string;
}

export interface RunSummary {
  total: number;
  compliant: number;
  deviation: number;
  unable_to_verify: number;
  requires_inspection: number;
  adherence_score: number | null;
}

export interface RunData {
  run_id: string;
  sop_steps: {
    run_id: string;
    sop_document: string;
    extracted_at: string;
    total_steps: number;
    steps: SopStep[];
  };
  checklist: {
    items: ChecklistItem[];
  };
  observations: {
    video_file: string;
    video_duration_seconds: number;
    analyzer_id: string;
    total_segments: number;
    segments: ObservationSegment[];
    analyzed_at?: string;
  };
  verdicts: RawVerdict[];
  adherence_score: number | null;
  summary: RunSummary;
  reviewer_overrides?: Record<string, ReviewOverride>;
}

export interface DashboardRow {
  item_id: string;
  step_id: string;
  sequence: number;
  section: string;
  criterion: string;
  check_type: string;
  reasoning: string;
  verdict: Verdict;
  confidence: number | null;
  confidence_pct: number | null;
  evidence_start: number | null;
  evidence_end: number | null;
  evidence_window: string;
  evidence_segment_id: string;
  keyframe_blob_path: string;
  sequence_ok: boolean | null;
  duration_ok: boolean | null;
  created_at: string;
  has_evidence: boolean;
  flags: string[];
  review_state: string;
  review_tone: 'success' | 'warning' | 'review' | 'neutral';
}

export interface NormalizedSegment {
  segment_id: string;
  start: number;
  end: number;
  window: string;
  action: string;
}

export interface AuditEvent {
  timestamp: string;
  sort_value: string | null; // Keep as string ISO format or parsed string
  actor: string;
  tone: 'info' | 'warning' | 'critical' | 'success';
  title: string;
  body: string;
}

export interface DashboardContext {
  run_id: string;
  sop_document: string;
  video_file: string;
  video_name: string;
  analyzer_id: string;
  created_at: string;
  created_at_raw: string;
  summary: RunSummary;
  rows: DashboardRow[];
  evidence_rows: DashboardRow[];
  confirmed_rows: DashboardRow[];
  attention_rows: DashboardRow[];
  deviation_rows: DashboardRow[];
  inspection_rows: DashboardRow[];
  unable_rows: DashboardRow[];
  compliant_rows: DashboardRow[];
  observation_segments: NormalizedSegment[];
  total_segments: number;
  duration: number;
  duration_text: string;
  total: number;
  compliant: number;
  deviation: number;
  unable_to_verify: number;
  requires_inspection: number;
  verifiable_total: number;
  abstention_total: number;
  review_queue_count: number;
  evidence_count: number;
  sequence_flags: number;
  duration_flags: number;
  score: number | null;
  score_pct: number | null;
  score_text: string;
  median_confidence: number | null;
  evidence_window_start: number | null;
  evidence_window_end: number | null;
  decision_title: string;
  decision_body: string;
  decision_action: string;
  workspace_status: string;
  workspace_tone: 'critical' | 'review' | 'clear';
  audit_events: AuditEvent[];
}
