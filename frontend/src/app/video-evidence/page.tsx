'use client';

import React from 'react';
import { useApp } from '../../lib/context';
import {
  Video20Regular,
  Info20Regular,
  CheckmarkCircle20Regular,
  ChevronRight20Regular
} from '@fluentui/react-icons';
import Link from 'next/link';

export default function VideoEvidencePage() {
  const { allRuns, isLoading, error } = useApp();

  const videos = React.useMemo(() => {
    return allRuns.map(run => {
      const obs = run.data.observations || {};
      const segments = obs.segments || [];
      const duration = obs.video_duration_seconds || 306.0;
      const srcName = obs.video_file || obs.video_url || '';

      // Check if video is pre-annotated
      const isAnnotated = srcName.toLowerCase().includes('annotated');

      return {
        runId: run.id,
        filename: srcName || 'video_footage.mp4',
        displayName: srcName ? srcName.replace(/\\/g, '/').split('/').pop() : 'video_footage.mp4',
        duration,
        durationText: `${Math.floor(duration / 60)}:${Math.round(duration % 60).toString().padStart(2, '0')}`,
        segmentsCount: obs.total_segments || segments.length,
        analyzerId: obs.analyzer_id || 'procedureguard_compliance_v1',
        isAnnotated,
        sopName: run.data.sop_steps?.sop_document || '-'
      };
    });
  }, [allRuns]);

  // Early returns AFTER all hooks (stable hook order across renders).
  if (isLoading) {
    return (
      <div className="p-6 flex flex-col gap-4 animate-pulse max-w-7xl mx-auto w-full select-none">
        <div className="h-8 bg-pg-surface-3 rounded w-1/4" />
        <div className="h-4 bg-pg-surface-3 rounded w-1/3 mt-2" />
        <div className="h-64 bg-pg-surface-3 rounded-pg-md border border-pg-hairline mt-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full select-none">
        <h1 className="text-xl font-semibold text-pg-ink">Error Loading Video Evidence</h1>
        <div className="p-4 bg-pg-semantic-error-bg border-l-4 border-pg-semantic-error rounded-pg-md text-xs text-pg-ink">
          <p className="font-bold">Failed to load video details:</p>
          <p className="mt-1 font-mono text-pg-ink-muted">{error}</p>
        </div>
      </div>
    );
  }

  if (allRuns.length === 0) {
    return (
      <div className="p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full select-none">
        <h1 className="text-xl font-semibold text-pg-ink">Video Evidence Library</h1>
        <div className="p-8 bg-pg-canvas border border-pg-hairline rounded-pg-md text-center flex flex-col items-center justify-center gap-3">
          <p className="text-sm font-semibold text-pg-ink">No video evidence available</p>
          <p className="text-xs text-pg-ink-muted">To view reports, run the ProcedureGuard pipeline script to populate the run store.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 flex flex-col gap-6 overflow-y-auto max-w-7xl mx-auto w-full select-none">
      
      {/* Page Header */}
      <section className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold text-pg-ink">
          Video Evidence Library
        </h1>
        <p className="text-xs text-pg-ink-muted leading-none">
          Audit video sources, timestamps, and camera frame extraction integrity.
        </p>
      </section>

      {/* Video Table Panel */}
      <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md overflow-hidden shadow-pg-subtle">
        <table className="w-full text-left border-collapse">
          <thead className="bg-pg-surface-2 border-b border-pg-hairline text-xs font-bold text-pg-ink-muted">
            <tr>
              <th className="px-4 py-2.5">Video File Name</th>
              <th className="px-4 py-2.5 w-32">Run Association</th>
              <th className="px-4 py-2.5 w-24">Duration</th>
              <th className="px-4 py-2.5 w-24">Segments</th>
              <th className="px-4 py-2.5 w-44">Analyzer Model</th>
              <th className="px-4 py-2.5 w-36">Integrity Status</th>
              <th className="px-4 py-2.5 w-12" />
            </tr>
          </thead>
          <tbody className="divide-y divide-pg-hairline text-xs text-pg-ink">
            {videos.map(video => (
              <tr key={video.runId} className="hover:bg-pg-surface-hover transition-colors">
                <td className="px-4 py-3.5">
                  <div className="flex items-center gap-2.5">
                    <Video20Regular className="text-pg-primary flex-shrink-0" />
                    <div className="flex flex-col">
                      <span className="font-semibold font-mono text-pg-ink truncate max-w-[280px]" title={video.filename}>
                        {video.displayName}
                      </span>
                      <span className="text-[10px] text-pg-ink-muted mt-0.5">Linked SOP: {video.sopName}</span>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3.5 font-mono font-semibold text-pg-ink-muted">
                  {video.runId}
                </td>
                <td className="px-4 py-3.5 font-semibold font-mono">
                  {video.durationText}
                </td>
                <td className="px-4 py-3.5 font-semibold font-mono">
                  {video.segmentsCount} zones
                </td>
                <td className="px-4 py-3.5 font-mono text-pg-ink-muted">
                  {video.analyzerId}
                </td>
                <td className="px-4 py-3.5">
                  {video.isAnnotated ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-pg-semantic-warning-bg text-pg-semantic-warning font-bold text-[9px] rounded-full uppercase tracking-wider">
                      Pre-Annotated
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-pg-semantic-success-bg text-pg-semantic-success font-bold text-[9px] rounded-full uppercase tracking-wider">
                      <CheckmarkCircle20Regular className="w-3.5 h-3.5" />
                      Raw Footage
                    </span>
                  )}
                </td>
                <td className="px-4 py-3.5 text-right">
                  <Link
                    href="/runs"
                    className="text-pg-ink-subtle hover:text-pg-primary transition-all cursor-pointer"
                    title="View verification run"
                  >
                    <ChevronRight20Regular />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Information Panel */}
      <div className="p-3 bg-pg-surface-2 border border-pg-hairline rounded-pg-md flex items-start gap-2.5 text-xs text-pg-ink">
        <Info20Regular className="text-pg-primary mt-0.5 flex-shrink-0" />
        <div className="flex flex-col gap-0.5">
          <span className="font-bold">Video Asset and Extraction Guidelines</span>
          <span className="text-pg-ink-muted text-[11px] leading-relaxed">
            All video clips uploaded are archived in the Azure Blob Storage <code>manufacturing-videos</code> container. Frame sampling is performed at a rate of 1 frame per second (fps). <strong>Security Warning:</strong> Verification run logs from pre-annotated video files are flagged loudly as they may violate regulatory auditing requirements.
          </span>
        </div>
      </div>
    </div>
  );
}
