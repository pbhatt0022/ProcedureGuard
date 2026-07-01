'use client';

import React from 'react';
import Link from 'next/link';
import { useApp } from '../lib/context';
import { motion } from 'framer-motion';
import {
  Board20Regular,
  TableSimple20Regular,
  Alert20Regular,
  PersonFeedback20Regular,
  ChevronRight20Regular,
  Info20Regular
} from '@fluentui/react-icons';

export default function Dashboard() {
  const { allRuns, reviewerOverrides, setActiveRunId, isLoading, error } = useApp();

  if (isLoading) {
    return (
      <div className="py-8 px-8 flex flex-col gap-8 animate-pulse max-w-7xl mx-auto w-full select-none">
        <section className="flex flex-col gap-1.5 mb-2">
          <div className="h-8 bg-pg-surface-3 rounded w-1/4" />
          <div className="h-4 bg-pg-surface-3 rounded w-1/3 mt-2" />
        </section>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-24 bg-pg-surface-3 rounded-pg-md border border-pg-hairline" />
          ))}
        </div>
        <div className="h-64 bg-pg-surface-3 rounded-pg-md border border-pg-hairline mt-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 px-8 flex flex-col gap-6 max-w-7xl mx-auto w-full select-none">
        <section className="flex flex-col gap-1.5 mb-2">
          <h1 className="text-2xl font-bold tracking-tight text-pg-ink">Error Loading Dashboard</h1>
        </section>
        <div className="p-4 bg-pg-semantic-error-bg border-l-4 border-pg-semantic-error rounded-pg-md text-xs text-pg-ink">
          <p className="font-bold">Failed to load run data:</p>
          <p className="mt-1 font-mono text-pg-ink-muted">{error}</p>
        </div>
      </div>
    );
  }

  if (allRuns.length === 0) {
    return (
      <div className="py-8 px-8 flex flex-col gap-6 max-w-7xl mx-auto w-full select-none">
        <section className="flex flex-col gap-1.5 mb-2">
          <h1 className="text-2xl font-bold tracking-tight text-pg-ink">ProcedureGuard Console</h1>
        </section>
        <div className="p-8 bg-pg-canvas border border-pg-hairline rounded-pg-md text-center flex flex-col items-center justify-center gap-3">
          <p className="text-sm font-semibold text-pg-ink">No runs available</p>
          <p className="text-xs text-pg-ink-muted">To view reports, run the ProcedureGuard pipeline script to populate the run store.</p>
        </div>
      </div>
    );
  }

  // Compute stats across all runs
  const runStats = allRuns.map(run => {
    const runId = run.id;
    const rawData = run.data;
    
    // Count items and overrides
    const checklistItems = rawData.checklist?.items || [];
    const verdicts = rawData.verdicts || [];
    const sourceRows: any[] = verdicts.length > 0 ? verdicts : checklistItems;
    
    const overrides = reviewerOverrides[runId] || {};

    let compliant = 0;
    let deviation = 0;
    let unable = 0;
    let inspection = 0;

    sourceRows.forEach(entry => {
      const itemId = entry.item_id;
      const override = overrides[itemId];
      const verdict = override ? override.verdict : (entry.verdict || 'Pending');

      if (verdict === 'Compliant') compliant++;
      else if (verdict === 'Deviation Detected') deviation++;
      else if (verdict === 'Unable to Verify') unable++;
      else if (verdict === 'Requires Inspection') inspection++;
    });

    const verifiableTotal = compliant + deviation;
    const score = verifiableTotal > 0 ? compliant / verifiableTotal : 0;
    const scorePct = Math.round(score * 100);

    const reviewQueueCount = deviation + unable + inspection;
    
    let status = 'Ready for export';
    let tone: 'success' | 'warning' | 'critical' = 'success';

    if (deviation > 0) {
      status = 'Deviation review required';
      tone = 'critical';
    } else if (inspection > 0) {
      status = 'Manual inspection required';
      tone = 'warning';
    } else if (unable > 0) {
      status = 'Coverage review required';
      tone = 'warning';
    }

    return {
      id: runId,
      sop: rawData.sop_steps?.sop_document || '-',
      video: rawData.observations?.video_file || '-',
      scorePct,
      compliant,
      deviation,
      unable,
      inspection,
      reviewQueueCount,
      status,
      tone
    };
  });

  const totalDeviations = runStats.reduce((sum, r) => sum + r.deviation, 0);
  const totalInspection = runStats.reduce((sum, r) => sum + r.inspection, 0);
  const totalUnable = runStats.reduce((sum, r) => sum + r.unable, 0);
  const totalReviewBacklog = runStats.reduce((sum, r) => sum + r.reviewQueueCount, 0);

  return (
    <div className="py-8 px-8 flex flex-col gap-8 overflow-y-auto max-w-7xl mx-auto w-full select-none">
      
      {/* Page Header */}
      <section className="flex flex-col gap-1.5 mb-2">
        <h1 className="text-2xl font-bold tracking-tight text-pg-ink">
          ProcedureGuard Console
        </h1>
        <p className="text-xs text-pg-ink-muted">
          Manufacturing compliance and visual evidence validation dashboard.
        </p>
      </section>

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-5">
        
        {/* Total Runs Card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.05, ease: [0.23, 1, 0.32, 1] }}
          whileHover={{ y: -2, boxShadow: "var(--shadow-pg-card)", borderColor: "var(--color-pg-primary-border-subtle)" }}
          className="p-5 bg-pg-surface-1 border border-pg-hairline rounded-pg-md flex flex-col justify-between min-h-[124px] transition-all duration-200 hover:bg-pg-surface-hover cursor-default shadow-pg-subtle"
        >
          <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Active Runs</span>
          <span className="text-4xl font-extrabold text-pg-ink font-display">{allRuns.length}</span>
          <span className="text-[10px] text-pg-ink-subtle">Total recorded runs in storage</span>
        </motion.div>

        {/* Total Deviations Card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.1, ease: [0.23, 1, 0.32, 1] }}
          whileHover={{ y: -2, boxShadow: "var(--shadow-pg-card)", borderColor: "rgba(209, 52, 56, 0.3)" }}
          className="p-5 bg-pg-semantic-error-bg/15 border border-pg-semantic-error/10 rounded-pg-md flex flex-col justify-between min-h-[124px] transition-all duration-200 hover:bg-pg-semantic-error-bg/25 cursor-default shadow-pg-subtle"
        >
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-pg-semantic-error uppercase tracking-wider">Active Deviations</span>
            <Alert20Regular className="text-pg-semantic-error" />
          </div>
          <span className="text-4xl font-extrabold text-pg-semantic-error font-display">{totalDeviations}</span>
          <span className="text-[10px] text-pg-ink-subtle">Requires supervisor nonconformance report</span>
        </motion.div>

        {/* Human Review Queue Depth Card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.15, ease: [0.23, 1, 0.32, 1] }}
          whileHover={{ y: -2, boxShadow: "var(--shadow-pg-card)", borderColor: "rgba(92, 46, 145, 0.3)" }}
          className="p-5 bg-pg-semantic-review-bg/15 border border-pg-semantic-review/10 rounded-pg-md flex flex-col justify-between min-h-[124px] transition-all duration-200 hover:bg-pg-semantic-review-bg/25 cursor-default shadow-pg-subtle"
        >
          <div className="flex justify-between items-center">
            <span className="text-[10px] font-bold text-pg-semantic-review uppercase tracking-wider">Review Backlog</span>
            <PersonFeedback20Regular className="text-pg-semantic-review" />
          </div>
          <span className="text-4xl font-extrabold text-pg-semantic-review font-display">{totalReviewBacklog}</span>
          <span className="text-[10px] text-pg-ink-subtle">Deviation / Inspection / Gaps queue depth</span>
        </motion.div>

        {/* Adherence Average Card */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: 0.2, ease: [0.23, 1, 0.32, 1] }}
          whileHover={{ y: -2, boxShadow: "var(--shadow-pg-card)", borderColor: "var(--color-pg-primary-border-subtle)" }}
          className="p-5 bg-pg-primary-subtle/30 border border-pg-primary-border-subtle/40 rounded-pg-md flex flex-col justify-between min-h-[124px] transition-all duration-200 hover:bg-pg-primary-subtle/50 cursor-default shadow-pg-subtle"
        >
          <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Compliance Trend</span>
          <div className="flex items-end justify-between">
            <span className="text-4xl font-extrabold text-pg-ink font-display">
              {Math.round(runStats.reduce((sum, r) => sum + r.scorePct, 0) / runStats.length)}%
            </span>
            
            {/*Restrained SVG trend sparkline */}
            <svg className="w-16 h-8 text-pg-primary mb-1" viewBox="0 0 100 30" fill="none">
              <path
                d="M 5,25 L 35,22 L 65,10 L 95,5"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="95" cy="5" r="3" className="fill-pg-primary" />
            </svg>
          </div>
          <span className="text-[10px] text-pg-ink-subtle">Average score of verifiable steps</span>
        </motion.div>
      </div>

      {/* Main Panel layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-2">
        
        {/* Left Column: Recent runs */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-pg-ink-muted uppercase tracking-wider">Recent Verification Runs</h2>
            <Link href="/runs" className="text-xs text-pg-primary font-semibold hover:underline flex items-center gap-0.5">
              <span>View all runs</span>
              <ChevronRight20Regular className="w-4.5 h-4.5" />
            </Link>
          </div>

          <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md overflow-hidden shadow-pg-subtle">
            <table className="w-full text-left border-collapse">
              <thead className="bg-pg-surface-2 border-b border-pg-hairline text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider h-10">
                <tr>
                  <th className="px-5 py-3 w-48 font-mono">Run ID</th>
                  <th className="px-5 py-3">SOP Reference</th>
                  <th className="px-5 py-3 w-24">Adherence</th>
                  <th className="px-5 py-3 w-44">Workspace Status</th>
                  <th className="px-5 py-3 w-12" />
                </tr>
              </thead>
              <tbody className="divide-y divide-pg-hairline text-xs text-pg-ink">
                {runStats.map(run => (
                  <tr key={run.id} className="hover:bg-pg-surface-hover transition-all duration-150">
                    <td className="px-5 py-4 font-mono font-semibold text-pg-ink">
                      <Link
                        href={`/runs?run=${run.id}`}
                        onClick={() => setActiveRunId(run.id)}
                        className="hover:underline hover:text-pg-primary"
                      >
                        {run.id}
                      </Link>
                    </td>
                    <td className="px-5 py-4 font-medium">
                      <div className="truncate max-w-[220px]" title={run.sop}>
                        {run.sop}
                      </div>
                      <div className="text-[10px] text-pg-ink-subtle truncate max-w-[220px] mt-1">
                        {run.video}
                      </div>
                    </td>
                    <td className="px-5 py-4 font-bold tabular-nums">
                      {run.scorePct}%
                    </td>
                    <td className="px-5 py-4">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[10px] ${
                        run.tone === 'critical'
                          ? 'bg-pg-semantic-error-bg text-pg-semantic-error'
                          : run.tone === 'warning'
                            ? 'bg-pg-semantic-review-bg text-pg-semantic-review'
                            : 'bg-pg-semantic-success-bg text-pg-semantic-success'
                      }`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        href={`/runs?run=${run.id}`}
                        onClick={() => setActiveRunId(run.id)}
                        className="text-pg-ink-subtle hover:text-pg-primary cursor-pointer transition-all"
                        title="View run evidence"
                      >
                        <ChevronRight20Regular />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column: Review Queue Backlog Summary */}
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-pg-ink-muted uppercase tracking-wider">Backlog Queue</h2>
            <Link href="/runs?tab=REVIEW" className="text-xs text-pg-primary font-semibold hover:underline flex items-center gap-0.5">
              <span>Open queue</span>
              <ChevronRight20Regular className="w-4.5 h-4.5" />
            </Link>
          </div>

          <div className="bg-pg-canvas border border-pg-hairline p-5 rounded-pg-md flex flex-col gap-5 shadow-pg-subtle">
            <div className="flex flex-col gap-1.5">
              <span className="text-sm font-bold text-pg-ink">Human review checklist items</span>
              <span className="text-xs text-pg-ink-muted leading-relaxed">Verification deviations, camera coverage holes, and fine-detail inspection steps requiring human sign-off.</span>
            </div>

            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between p-3.5 bg-pg-surface-2 rounded-pg-sm border border-pg-hairline hover:bg-pg-surface-3 transition-colors duration-150">
                <div className="flex items-center gap-2.5 text-xs font-semibold text-pg-ink">
                  <span className="w-2.5 h-2.5 rounded-full bg-pg-semantic-error" />
                  <span>Unresolved Deviations</span>
                </div>
                <span className="font-bold tabular-nums text-pg-semantic-error text-sm font-display">{totalDeviations}</span>
              </div>

              <div className="flex items-center justify-between p-3.5 bg-pg-surface-2 rounded-pg-sm border border-pg-hairline hover:bg-pg-surface-3 transition-colors duration-150">
                <div className="flex items-center gap-2.5 text-xs font-semibold text-pg-ink">
                  <span className="w-2.5 h-2.5 rounded-full bg-pg-semantic-review" />
                  <span>Manual Inspections</span>
                </div>
                <span className="font-bold tabular-nums text-pg-semantic-review text-sm font-display">{totalInspection}</span>
              </div>

              <div className="flex items-center justify-between p-3.5 bg-pg-surface-2 rounded-pg-sm border border-pg-hairline hover:bg-pg-surface-3 transition-colors duration-150">
                <div className="flex items-center gap-2.5 text-xs font-semibold text-pg-ink">
                  <span className="w-2.5 h-2.5 rounded-full bg-pg-semantic-warning" />
                  <span>Coverage Gaps (Unable)</span>
                </div>
                <span className="font-bold tabular-nums text-pg-semantic-warning text-sm font-display">{totalUnable}</span>
              </div>
            </div>

            <Link
              href="/runs?tab=REVIEW"
              className="text-center text-xs font-bold text-white py-3 rounded-pg-sm bg-pg-primary hover:bg-pg-primary-hover active:scale-[0.98] transition-all shadow-pg-subtle mt-2 btn-tactile"
            >
              Start Review Session
            </Link>
          </div>
        </div>
      </div>
      
      {/* Informational Section */}
      <div className="p-5 bg-pg-surface-2 border border-pg-hairline rounded-pg-md flex items-start gap-3 text-xs text-pg-ink mt-4 shadow-pg-subtle">
        <Info20Regular className="text-pg-primary mt-0.5 flex-shrink-0" />
        <div className="flex flex-col gap-1.5">
          <span className="font-bold">Compliance Standard Alignment (ISO 13485 / FDA Title 21 CFR Part 820)</span>
          <span className="text-pg-ink-muted text-[11px] leading-relaxed">
            Every step execution logged in this console preserves continuous cryptographic trace linkage to source frame blobs, video hash, SOP PDF metadata, and the reviewer's authorization identity. Overriding a model verdict updates the audit trail dynamically but does not delete system records.
          </span>
        </div>
      </div>
    </div>
  );
}
