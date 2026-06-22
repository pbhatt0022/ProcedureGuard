'use client';

import React, { createContext, useContext, useState, useEffect, useMemo } from 'react';
import { RunData, DashboardContext, Verdict, DashboardRow, ReviewOverride } from './types';
import { buildDashboardContext } from './normalizer';

export interface RunOverrideState {
  [itemId: string]: ReviewOverride;
}

export interface ReviewOverridesState {
  [runId: string]: RunOverrideState;
}

interface AppContextType {
  activeRunId: string;
  setActiveRunId: (id: string) => void;
  rawRunData: RunData | null;
  normalizedCtx: DashboardContext | null;
  allRuns: { id: string; name: string; data: RunData; description: string }[];
  reviewerOverrides: ReviewOverridesState;
  updateReviewerOverride: (itemId: string, override: Partial<ReviewOverride>) => void;
  isNavCollapsed: boolean;
  setIsNavCollapsed: (collapsed: boolean) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  isLoading: boolean;
  error: string | null;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [allRuns, setAllRuns] = useState<{ id: string; name: string; data: RunData; description: string }[]>([]);
  const [activeRunId, setActiveRunId] = useState<string>('');
  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Track reviewer overrides: runId -> itemId -> override details
  const [reviewerOverrides, setReviewerOverrides] = useState<ReviewOverridesState>({});

  // Load runs from the API route on mount
  useEffect(() => {
    async function fetchRuns() {
      try {
        setIsLoading(true);
        setError(null);
        
        const res = await fetch('/api/runs');
        if (!res.ok) {
          throw new Error(`Failed to list runs: ${res.statusText}`);
        }
        
        const summaries = await res.json();
        if (!Array.isArray(summaries)) {
          throw new Error('Invalid runs data format returned from API');
        }

        if (summaries.length === 0) {
          setAllRuns([]);
          setIsLoading(false);
          return;
        }

        // Fetch detailed data for all runs in parallel
        const detailedRuns = await Promise.all(
          summaries.map(async (summary: any) => {
            const runRes = await fetch(`/api/runs/${summary.id}`);
            if (!runRes.ok) {
              throw new Error(`Failed to fetch run data for ${summary.id}`);
            }
            const data = await runRes.json();
            return {
              id: summary.id,
              name: summary.name,
              description: summary.description || '',
              data: data as RunData
            };
          })
        );

        setAllRuns(detailedRuns);

        // Initialize overrides state from run data
        const initialOverrides: ReviewOverridesState = {};
        detailedRuns.forEach(run => {
          if (run.data.reviewer_overrides) {
            initialOverrides[run.id] = run.data.reviewer_overrides;
          }
        });
        setReviewerOverrides(initialOverrides);

        // Try to default to Candidate 22 if present, otherwise default to first run
        const candidate22 = detailedRuns.find(r => r.id === 'run-20260618-1e0ebcb5');
        if (candidate22) {
          setActiveRunId(candidate22.id);
        } else if (detailedRuns.length > 0) {
          setActiveRunId(detailedRuns[0].id);
        }
      } catch (err: any) {
        console.error('Failed to load runs:', err);
        setError(err.message || 'Failed to load runs from server');
      } finally {
        setIsLoading(false);
      }
    }

    fetchRuns();
  }, []);

  // Get current raw data
  const rawRunData = useMemo(() => {
    if (isLoading || allRuns.length === 0) return null;
    const selected = allRuns.find(r => r.id === activeRunId);
    return selected ? selected.data : null;
  }, [activeRunId, allRuns, isLoading]);

  // Compute normalized context, applying overrides dynamically
  const normalizedCtx = useMemo(() => {
    if (!rawRunData) return null;
    
    const baseCtx = buildDashboardContext(rawRunData);
    const overrides = reviewerOverrides[activeRunId];
    
    if (!overrides) return baseCtx;

    // Apply overrides to rows
    const updatedRows = baseCtx.rows.map(row => {
      const override = overrides[row.item_id];
      if (!override) return row;

      // Update verdict and states
      const updatedRow = {
        ...row,
        verdict: override.verdict,
        reasoning: override.notes ? `${override.notes} (Reviewer note)` : row.reasoning,
        review_state: override.status,
        review_tone: (override.status === 'Confirmed compliant' 
          ? 'success' 
          : override.status === 'Confirmed deviation' 
            ? 'neutral' 
            : override.status === 'Escalated' 
              ? 'review' 
              : 'warning') as any
      };
      
      // Update flags
      const flags = [...row.flags].filter(f => f !== 'Inspection only' && f !== 'No visible confirmation');
      if (override.verdict === 'Requires Inspection') {
        flags.push('Inspection only');
      } else if (override.verdict === 'Unable to Verify') {
        flags.push('No visible confirmation');
      }
      updatedRow.flags = flags;

      return updatedRow;
    });

    // Recompute summary metrics
    const counts = {
      'Compliant': 0,
      'Deviation Detected': 0,
      'Unable to Verify': 0,
      'Requires Inspection': 0,
      'Pending': 0
    };
    for (const r of updatedRows) {
      counts[r.verdict] = (counts[r.verdict] || 0) + 1;
    }

    const total = updatedRows.length;
    const compliant = counts['Compliant'];
    const deviation = counts['Deviation Detected'];
    const unable = counts['Unable to Verify'];
    const inspection = counts['Requires Inspection'];

    const verifiableTotal = compliant + deviation;
    const score = verifiableTotal > 0 ? compliant / verifiableTotal : 0;
    const scorePct = Math.round(score * 100);

    const reviewQueueCount = updatedRows.filter(r => 
      r.review_state !== 'Auto-cleared' && 
      r.review_state !== 'Confirmed compliant' && 
      r.review_state !== 'Confirmed deviation' &&
      r.review_state !== 'Marked unable to verify'
    ).length;
    
    let workspaceStatus = 'Ready for export';
    let workspaceTone: 'critical' | 'review' | 'clear' = 'clear';

    if (deviation > 0) {
      workspaceStatus = 'Deviation review required';
      workspaceTone = 'critical';
    } else if (inspection > 0) {
      workspaceStatus = 'Manual inspection required';
      workspaceTone = 'review';
    } else if (unable > 0) {
      workspaceStatus = 'Coverage review required';
      workspaceTone = 'review';
    }

    if (reviewQueueCount > 0) {
      // Still needs action
    } else {
      workspaceStatus = 'Ready for export';
      workspaceTone = 'clear';
    }

    // Synthesize updated audit events
    const updatedCtx: DashboardContext = {
      ...baseCtx,
      rows: updatedRows,
      evidence_rows: updatedRows.filter(r => r.has_evidence),
      confirmed_rows: updatedRows.filter(r => r.verdict === 'Compliant'),
      attention_rows: updatedRows.filter(r => r.verdict !== 'Compliant'),
      deviation_rows: updatedRows.filter(r => r.verdict === 'Deviation Detected'),
      inspection_rows: updatedRows.filter(r => r.verdict === 'Requires Inspection'),
      unable_rows: updatedRows.filter(r => r.verdict === 'Unable to Verify'),
      compliant_rows: updatedRows.filter(r => r.verdict === 'Compliant'),
      total,
      compliant,
      deviation,
      unable_to_verify: unable,
      requires_inspection: inspection,
      verifiable_total: verifiableTotal,
      abstention_total: unable + inspection,
      review_queue_count: reviewQueueCount,
      score,
      score_pct: scorePct,
      score_text: `${scorePct}%`,
      workspace_status: workspaceStatus,
      workspace_tone: workspaceTone,
    };

    // Append audit events representing reviewer actions
    const auditEvents = [...baseCtx.audit_events];
    Object.entries(overrides).forEach(([itemId, override]) => {
      auditEvents.push({
        timestamp: override.timestamp,
        sort_value: override.timestamp,
        actor: override.reviewer,
        tone: override.status === 'Confirmed compliant' ? 'success' : override.status === 'Escalated' ? 'warning' : 'info',
        title: `${itemId} review signed off`,
        body: `Verdict set to ${override.verdict}. Notes: "${override.notes || 'None'}". Status: ${override.status}.`
      });
    });

    auditEvents.sort((a, b) => {
      if (a.sort_value === null && b.sort_value === null) return a.title.localeCompare(b.title);
      if (a.sort_value === null) return 1;
      if (b.sort_value === null) return -1;
      const cmp = a.sort_value.localeCompare(b.sort_value);
      if (cmp !== 0) return cmp;
      return a.title.localeCompare(b.title);
    });

    updatedCtx.audit_events = auditEvents;

    return updatedCtx;
  }, [rawRunData, activeRunId, reviewerOverrides]);

  const updateReviewerOverride = (itemId: string, override: Partial<ReviewOverride>) => {
    const runOverrides = reviewerOverrides[activeRunId] || {};
    const existing = runOverrides[itemId] || {
      verdict: 'Pending',
      notes: '',
      reviewer: 'Vikram Nair (QA Manager)',
      timestamp: new Date().toISOString(),
      status: 'In review'
    };

    const statusMap: Record<string, ReviewOverride['status']> = {
      'Compliant': 'Confirmed compliant',
      'Deviation Detected': 'Confirmed deviation',
      'Unable to Verify': 'Marked unable to verify',
      'Requires Inspection': 'In review'
    };

    const newVerdict = override.verdict ?? existing.verdict;
    const defaultStatus = statusMap[newVerdict] ?? 'In review';

    const updated: ReviewOverride = {
      ...existing,
      ...override,
      verdict: newVerdict,
      status: override.status ?? defaultStatus,
      timestamp: new Date().toISOString()
    };

    setReviewerOverrides(prev => ({
      ...prev,
      [activeRunId]: {
        ...(prev[activeRunId] || {}),
        [itemId]: updated
      }
    }));

    // Persist override to filesystem runs store asynchronously
    fetch(`/api/runs/${activeRunId}/review`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ itemId, override: updated })
    }).catch(err => {
      console.error('Failed to save reviewer override on server:', err);
    });
  };

  return (
    <AppContext.Provider value={{
      activeRunId,
      setActiveRunId,
      rawRunData,
      normalizedCtx,
      allRuns,
      reviewerOverrides,
      updateReviewerOverride,
      isNavCollapsed,
      setIsNavCollapsed,
      searchQuery,
      setSearchQuery,
      isLoading,
      error
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
