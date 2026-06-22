'use client';

import React from 'react';
import { useApp } from '../../lib/context';
import { formatConfidence, formatDuration } from '../../lib/normalizer';
import {
  DocumentArrowDown20Regular,
  Print20Regular,
  Info20Regular
} from '@fluentui/react-icons';

export default function ExportPage() {
  const { normalizedCtx, activeRunId, isLoading, error } = useApp();

  if (isLoading) {
    return (
      <div className="p-6 flex flex-col gap-4 animate-pulse max-w-5xl mx-auto w-full select-none">
        <div className="h-8 bg-pg-surface-3 rounded w-1/4" />
        <div className="h-4 bg-pg-surface-3 rounded w-1/3 mt-2" />
        <div className="h-64 bg-pg-surface-3 rounded-pg-md border border-pg-hairline mt-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col gap-6 max-w-5xl mx-auto w-full select-none">
        <h1 className="text-xl font-semibold text-pg-ink">Error Loading Report</h1>
        <div className="p-4 bg-pg-semantic-error-bg border-l-4 border-pg-semantic-error rounded-pg-md text-xs text-pg-ink">
          <p className="font-bold">Failed to load run details:</p>
          <p className="mt-1 font-mono text-pg-ink-muted">{error}</p>
        </div>
      </div>
    );
  }

  if (!normalizedCtx) {
    return (
      <div className="p-6 flex flex-col gap-6 max-w-5xl mx-auto w-full select-none">
        <h1 className="text-xl font-semibold text-pg-ink">Archival Report</h1>
        <div className="p-8 bg-pg-canvas border border-pg-hairline rounded-pg-md text-center flex flex-col items-center justify-center gap-3">
          <p className="text-sm font-semibold text-pg-ink">No report data available</p>
          <p className="text-xs text-pg-ink-muted">To view reports, run the ProcedureGuard pipeline script to populate the run store.</p>
        </div>
      </div>
    );
  }

  const isWorkspaceClean = normalizedCtx.review_queue_count === 0;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="p-6 flex flex-col gap-6 overflow-y-auto max-w-5xl mx-auto w-full select-none">
      
      {/* Top action header (hidden on print) */}
      <section className="bg-pg-canvas border border-pg-hairline p-4 rounded-pg-md flex flex-wrap items-center justify-between gap-4 shadow-pg-subtle print:hidden">
        <div className="flex flex-col gap-0.5">
          <span className="text-xs font-bold text-pg-ink-muted uppercase tracking-wider font-mono">Archival Document Preview</span>
          <span className="text-sm font-bold text-pg-ink">
            {isWorkspaceClean 
              ? 'Ready for Archival Sign-off' 
              : `Draft Report — ${normalizedCtx.review_queue_count} unresolved review items`
            }
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button 
            onClick={handlePrint}
            className="flex items-center gap-2 text-xs text-pg-ink font-semibold px-3 py-1.5 border border-pg-hairline-strong rounded-pg-sm bg-pg-canvas hover:bg-pg-surface-hover active:scale-[0.98] transition-all cursor-pointer"
          >
            <Print20Regular />
            <span>Print or Save PDF</span>
          </button>
          <button 
            onClick={() => alert("CSV exported successfully (mocked).")}
            className="flex items-center gap-2 text-xs text-pg-ink font-semibold px-3 py-1.5 border border-pg-hairline-strong rounded-pg-sm bg-pg-canvas hover:bg-pg-surface-hover active:scale-[0.98] transition-all cursor-pointer"
          >
            <DocumentArrowDown20Regular />
            <span>Export CSV file</span>
          </button>
        </div>
      </section>

      {/* Audit Report Document Sheet */}
      <article className="relative bg-pg-canvas border border-pg-hairline rounded-pg-md p-8 shadow-pg-card flex flex-col gap-6 font-sans text-pg-ink select-text print:border-none print:shadow-none print:p-0 print:text-black">
        
        {/* Draft Watermark */}
        {!isWorkspaceClean && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden select-none opacity-[0.03] print:opacity-[0.04]">
            <span className="text-[120px] font-black text-pg-semantic-error border-[16px] border-pg-semantic-error p-8 rounded-pg-xl rotate-[-25deg]">
              DRAFT
            </span>
          </div>
        )}

        {/* Document Header */}
        <div className="flex justify-between items-start border-b border-pg-hairline pb-4">
          <div className="flex flex-col gap-1">
            <h1 className="text-base font-bold uppercase tracking-wider text-pg-ink print:text-black leading-none">
              ProcedureGuard Compliance Record
            </h1>
            <span className="text-xs text-pg-ink-muted print:text-gray-600">
              Automated computer-vision verification report
            </span>
          </div>
          <div className="flex flex-col items-end gap-0.5 text-right font-mono text-[10px] text-pg-ink-subtle print:text-gray-500">
            <span>RUN: {normalizedCtx.run_id}</span>
            <span>DATE: {normalizedCtx.created_at}</span>
            <span>STATUS: {isWorkspaceClean ? 'FINALIZED' : 'DRAFT'}</span>
          </div>
        </div>

        {/* Run Metadata Grid */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-pg-surface-2 p-4 rounded-pg-md print:bg-gray-100 print:text-black">
          <div className="flex flex-col gap-0.5">
            <span className="text-[9px] font-bold text-pg-ink-muted uppercase tracking-wider print:text-gray-500">SOP Document</span>
            <span className="text-xs font-semibold">{normalizedCtx.sop_document}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[9px] font-bold text-pg-ink-muted uppercase tracking-wider print:text-gray-500">Video Source</span>
            <span className="text-xs font-semibold truncate max-w-[150px] font-mono" title={normalizedCtx.video_file}>
              {normalizedCtx.video_name}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[9px] font-bold text-pg-ink-muted uppercase tracking-wider print:text-gray-500">Adherence Score</span>
            <span className="text-xs font-bold text-pg-primary print:text-black">{normalizedCtx.score_text}</span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[9px] font-bold text-pg-ink-muted uppercase tracking-wider print:text-gray-500">Verifiable Steps</span>
            <span className="text-xs font-semibold">{normalizedCtx.compliant} of {normalizedCtx.verifiable_total} passed</span>
          </div>
        </section>

        {/* Limitations Notice */}
        <section className="p-3 bg-pg-semantic-info-bg/50 border-l-4 border-pg-semantic-info text-xs leading-relaxed text-pg-ink-muted print:border-gray-400 print:bg-transparent print:text-gray-600">
          <div className="font-bold text-pg-ink mb-0.5 print:text-black">Regulatory Limitations & human-review Notice</div>
          This verification record aggregates computer-vision pipeline outputs. System classifications do not guarantee final product conformance or regulatory compliance. Findings must be formally reviewed and signed off by an authorized quality systems supervisor before batch release.
        </section>

        {/* Step List Table */}
        <section className="flex flex-col gap-2.5">
          <h2 className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider print:text-black">Checklist Verdicts</h2>
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-pg-hairline font-bold text-pg-ink-muted print:text-black h-8">
                <th className="py-1 w-14 font-mono">Step</th>
                <th className="py-1">SOP Criterion</th>
                <th className="py-1 w-36">Verdict</th>
                <th className="py-1 w-20">Confidence</th>
                <th className="py-1 w-20">Timestamp</th>
                <th className="py-1 w-28">Reviewer Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-pg-hairline">
              {normalizedCtx.rows.map(row => (
                <tr key={row.item_id} className="h-8">
                  <td className="py-1.5 font-mono font-semibold">{row.step_id}</td>
                  <td className="py-1.5 pr-4 text-pg-ink print:text-black font-medium">{row.criterion}</td>
                  <td className="py-1.5 font-bold">
                    <span className={
                      row.verdict === 'Compliant'
                        ? 'text-pg-semantic-success'
                        : row.verdict === 'Deviation Detected'
                          ? 'text-pg-semantic-error'
                          : row.verdict === 'Unable to Verify'
                            ? 'text-pg-semantic-warning'
                            : 'text-pg-semantic-review'
                    }>
                      {row.verdict}
                    </span>
                  </td>
                  <td className="py-1.5 font-mono text-pg-ink-muted print:text-gray-500">{formatConfidence(row.confidence)}</td>
                  <td className="py-1.5 font-mono">{row.evidence_start !== null ? formatDuration(row.evidence_start) : '-'}</td>
                  <td className="py-1.5 font-medium">{row.review_state}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>

        {/* Supervisor Sign-off Footer */}
        <section className="border-t border-pg-hairline pt-6 mt-6 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-6 print:text-black">
          <div className="flex flex-col gap-1 text-xs">
            <span className="font-bold">QA Manager Certification Signature:</span>
            <span className="text-pg-ink-muted print:text-gray-600">
              {isWorkspaceClean 
                ? 'Certified electronically by Vikram Nair (QA Manager)' 
                : 'Pending Supervisor review signatures — Draft status'
              }
            </span>
          </div>
          <div className="flex flex-col items-start sm:items-end gap-1 text-xs">
            <div className="h-10 w-48 border-b border-pg-hairline-strong relative">
              {isWorkspaceClean && (
                <span className="absolute bottom-1 left-2 font-mono italic text-sm text-pg-primary font-bold">
                  /Vikram Nair/
                </span>
              )}
            </div>
            <span className="text-[9px] font-bold text-pg-ink-muted uppercase tracking-wider print:text-gray-500">Signature stamp</span>
          </div>
        </section>
      </article>
    </div>
  );
}
