import fs from 'fs';
import path from 'path';
import { RunData } from './types';

export interface RunSummary {
  id: string;
  name: string;
  description: string;
  created_at: string;
  adherence_score: number | null;
}

// Resolve runs directory absolutely using path.resolve to avoid CWD coupling.
// Default runs directory is resolved relative to this workspace root: <repo>/runs.
const RUNS_DIR = process.env.PROCEDUREGUARD_RUNS_DIR
  ? path.resolve(process.env.PROCEDUREGUARD_RUNS_DIR)
  : path.resolve(process.cwd(), '..', 'runs');

// Map metadata for the three demo runs so their UI labels match the original specification
const DEMO_METADATA: Record<string, { name: string; description: string }> = {
  'run-20260618-1e0ebcb5': {
    name: 'IndustReal honest mix (Candidate 22)',
    description: 'Mixed evidence with explicit abstentions and inspection-only checks.'
  },
  'run-20260618-da40bd3c': {
    name: 'IndustReal baseline (Baseline 23)',
    description: 'Reference report from the IndustReal evaluation set.'
  },
  'run-20260616-5b0b97e6': {
    name: 'IndustReal candidate (Candidate 16)',
    description: 'Additional candidate run for comparing evidence density and review posture.'
  }
};

function getMetadataForRun(runId: string, docName: string) {
  if (DEMO_METADATA[runId]) {
    return DEMO_METADATA[runId];
  }
  return {
    name: `Run ${runId.slice(0, 12)}...`,
    description: `Automated compliance verification report for ${docName || 'SOP'}.`
  };
}

export async function listRuns(): Promise<RunSummary[]> {
  if (!fs.existsSync(RUNS_DIR)) {
    return [];
  }

  const files = fs.readdirSync(RUNS_DIR);
  const runs: RunSummary[] = [];

  for (const file of files) {
    if (!file.endsWith('.json')) continue;

    try {
      const filePath = path.join(RUNS_DIR, file);
      const content = fs.readFileSync(filePath, 'utf-8');
      const data = JSON.parse(content) as RunData;

      const runId = data.run_id;
      if (!runId) continue;

      const docName = data.sop_steps?.sop_document || '';
      const meta = getMetadataForRun(runId, docName);

      // Extract a created timestamp or use file stat
      let created_at = new Date().toISOString();
      if (data.sop_steps?.extracted_at) {
        created_at = data.sop_steps.extracted_at;
      } else {
        const stats = fs.statSync(filePath);
        created_at = stats.birthtime.toISOString();
      }

      runs.push({
        id: runId,
        name: meta.name,
        description: meta.description,
        created_at,
        adherence_score: data.adherence_score ?? null
      });
    } catch (err) {
      console.error(`Failed to parse run file ${file}:`, err);
    }
  }

  // Sort by created_at descending (newest first)
  return runs.sort((a, b) => b.created_at.localeCompare(a.created_at));
}

export async function getRun(runId: string): Promise<RunData | null> {
  // Prevent path traversal
  if (!/^run-[\w-]+$/.test(runId)) {
    console.warn(`Blocked invalid runId path traversal attempt: ${runId}`);
    return null;
  }

  const filePath = path.join(RUNS_DIR, `${runId}.json`);
  if (!fs.existsSync(filePath)) {
    return null;
  }

  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    const runData = JSON.parse(content) as RunData;

    // Load reviewer overrides from the sidecar file if it exists, keeping the main run file pristine
    const reviewPath = path.join(RUNS_DIR, `${runId}.review.json`);
    if (fs.existsSync(reviewPath)) {
      try {
        const reviewContent = fs.readFileSync(reviewPath, 'utf-8');
        const reviewData = JSON.parse(reviewContent);
        runData.reviewer_overrides = reviewData.reviewer_overrides || {};
      } catch (sidecarErr) {
        console.error(`Failed to load review overrides sidecar for ${runId}:`, sidecarErr);
      }
    }

    return runData;
  } catch (err) {
    console.error(`Failed to read run file ${runId}:`, err);
    return null;
  }
}

/**
 * Note on Concurrency:
 * This performs a whole-file read-modify-write on the review sidecar file
 * without locks or write-serialization. For a single-user local demo, this
 * last-write-wins model is sufficient, but will need transaction locks
 * or optimistic concurrency checks when migrated to Cosmos DB (B4).
 */
export async function updateRun(runId: string, data: Partial<RunData>): Promise<boolean> {
  // Prevent path traversal
  if (!/^run-[\w-]+$/.test(runId)) {
    console.warn(`Blocked invalid runId path traversal attempt in updateRun: ${runId}`);
    return false;
  }

  const reviewPath = path.join(RUNS_DIR, `${runId}.review.json`);
  
  try {
    let currentOverrides = {};
    if (fs.existsSync(reviewPath)) {
      try {
        const content = fs.readFileSync(reviewPath, 'utf-8');
        const parsed = JSON.parse(content);
        currentOverrides = parsed.reviewer_overrides || {};
      } catch (readErr) {
        console.warn(`Could not read existing sidecar file, creating fresh overrides:`, readErr);
      }
    }

    // Merge new overrides
    const newOverrides = {
      ...currentOverrides,
      ...(data as any).reviewer_overrides
    };

    const reviewData = {
      run_id: runId,
      updated_at: new Date().toISOString(),
      reviewer_overrides: newOverrides
    };

    // Save strictly to the sidecar file, keeping runs/<runId>.json pristine
    fs.writeFileSync(reviewPath, JSON.stringify(reviewData, null, 2), 'utf-8');
    return true;
  } catch (err) {
    console.error(`Failed to write reviewer override sidecar for ${runId}:`, err);
    return false;
  }
}

