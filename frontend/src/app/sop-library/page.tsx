'use client';

import React, { useState } from 'react';
import { useApp } from '../../lib/context';
import {
  DocumentBulletList20Regular,
  DocumentArrowDown20Regular,
  Info20Regular,
  ArrowRight20Regular
} from '@fluentui/react-icons';

export default function SopLibraryPage() {
  const { allRuns, isLoading, error } = useApp();

  const [selectedSopName, setSelectedSopName] = useState<string | null>(null);

  // Compile unique SOPs from the runs
  const sops = React.useMemo(() => {
    const uniqueSops: Record<string, any> = {};
    allRuns.forEach(run => {
      const docName = run.data.sop_steps?.sop_document;
      if (!docName || uniqueSops[docName]) return;

      const steps = run.data.sop_steps?.steps || [];
      const totalSteps = run.data.sop_steps?.total_steps || steps.length;
      
      const presenceChecks = steps.filter(s => s.check_type === 'presence').length;
      const sequenceChecks = steps.filter(s => s.check_type === 'sequence').length;
      const detailChecks = steps.filter(s => s.check_type === 'fine_detail').length;

      uniqueSops[docName] = {
        name: docName,
        extractedAt: run.data.sop_steps?.extracted_at,
        totalSteps,
        presenceChecks,
        sequenceChecks,
        detailChecks,
        steps: steps.map(s => ({
          stepId: s.step_id,
          sequence: s.sequence,
          criterion: s.description,
          checkType: s.check_type,
          section: s.section
        }))
      };
    });

    return Object.values(uniqueSops);
  }, [allRuns]);

  // Set default selected SOP
  React.useEffect(() => {
    if (sops.length > 0 && !selectedSopName) {
      setSelectedSopName(sops[0].name);
    }
  }, [sops, selectedSopName]);

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
        <h1 className="text-xl font-semibold text-pg-ink">Error Loading SOP Library</h1>
        <div className="p-4 bg-pg-semantic-error-bg border-l-4 border-pg-semantic-error rounded-pg-md text-xs text-pg-ink">
          <p className="font-bold">Failed to load SOP details:</p>
          <p className="mt-1 font-mono text-pg-ink-muted">{error}</p>
        </div>
      </div>
    );
  }

  if (allRuns.length === 0) {
    return (
      <div className="p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full select-none">
        <h1 className="text-xl font-semibold text-pg-ink">SOP Library</h1>
        <div className="p-8 bg-pg-canvas border border-pg-hairline rounded-pg-md text-center flex flex-col items-center justify-center gap-3">
          <p className="text-sm font-semibold text-pg-ink">No SOPs available</p>
          <p className="text-xs text-pg-ink-muted">To view reports, run the ProcedureGuard pipeline script to populate the run store.</p>
        </div>
      </div>
    );
  }

  const activeSop = sops.find(s => s.name === selectedSopName) || sops[0] || null;

  return (
    <div className="p-6 flex flex-col gap-6 overflow-hidden h-full max-w-7xl mx-auto w-full select-none">
      
      {/* Page Header */}
      <section className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold text-pg-ink">
          SOP Library
        </h1>
        <p className="text-xs text-pg-ink-muted leading-none">
          Manage Standard Operating Procedure (SOP) files and verify automated checklist extraction coverage.
        </p>
      </section>

      {/* Main Split layout */}
      <div className="flex-1 flex flex-col md:flex-row gap-6 overflow-hidden">
        
        {/* Left Side: Ingested SOPs List */}
        <div className="flex-1 flex flex-col gap-3">
          <h2 className="text-xs font-bold text-pg-ink-muted uppercase tracking-wider">Ingested SOP Documents</h2>
          
          <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md overflow-hidden flex-1 shadow-pg-subtle overflow-y-auto">
            <table className="w-full text-left border-collapse">
              <thead className="bg-pg-surface-2 border-b border-pg-hairline sticky top-0 text-xs font-bold text-pg-ink-muted z-10">
                <tr>
                  <th className="px-4 py-2.5">Document Name</th>
                  <th className="px-4 py-2.5 w-24">Checklists</th>
                  <th className="px-4 py-2.5 w-44">Verifiability Tiers</th>
                  <th className="px-4 py-2.5 w-12" />
                </tr>
              </thead>
              <tbody className="divide-y divide-pg-hairline text-xs text-pg-ink">
                {sops.map(sop => (
                  <tr
                    key={sop.name}
                    onClick={() => setSelectedSopName(sop.name)}
                    className={`hover:bg-pg-surface-hover cursor-pointer transition-colors ${
                      selectedSopName === sop.name ? 'bg-pg-primary-subtle' : ''
                    }`}
                  >
                    <td className="px-4 py-3.5">
                      <div className="font-semibold text-pg-ink truncate max-w-[240px]" title={sop.name}>
                        {sop.name}
                      </div>
                      <div className="text-[10px] text-pg-ink-muted mt-0.5">
                        Ingested: {new Date(sop.extractedAt).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-4 py-3.5 font-semibold font-mono text-pg-ink-muted">
                      {sop.totalSteps} steps
                    </td>
                    <td className="px-4 py-3.5">
                      <div className="flex flex-col gap-1">
                        <div className="flex justify-between text-[10px] text-pg-ink-muted">
                          <span>Presence: <span className="font-semibold text-pg-ink">{sop.presenceChecks}</span></span>
                          <span>Sequence: <span className="font-semibold text-pg-ink">{sop.sequenceChecks}</span></span>
                          <span>Inspection: <span className="font-semibold text-pg-ink">{sop.detailChecks}</span></span>
                        </div>
                        <div className="h-1.5 w-full bg-pg-surface-3 rounded-full overflow-hidden flex">
                          <div style={{ width: `${(sop.presenceChecks / sop.totalSteps) * 100}%` }} className="bg-pg-semantic-success h-full" />
                          <div style={{ width: `${(sop.sequenceChecks / sop.totalSteps) * 100}%` }} className="bg-pg-primary h-full" />
                          <div style={{ width: `${(sop.detailChecks / sop.totalSteps) * 100}%` }} className="bg-pg-semantic-review h-full" />
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3.5 text-right">
                      <ArrowRight20Regular className={selectedSopName === sop.name ? 'text-pg-primary' : 'text-pg-ink-subtle'} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Side: Checklist Preview */}
        <div className="w-full md:w-[460px] flex flex-col gap-3">
          <h2 className="text-xs font-bold text-pg-ink-muted uppercase tracking-wider">Checklist Preview</h2>

          <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md flex-grow overflow-hidden flex flex-col p-4 gap-4 shadow-pg-subtle relative">
            {activeSop ? (
              <div className="flex-1 flex flex-col overflow-hidden gap-3">
                <div className="flex items-center justify-between border-b border-pg-hairline pb-2 flex-shrink-0">
                  <div className="flex flex-col">
                    <span className="text-xs font-bold text-pg-ink truncate max-w-[280px]" title={activeSop.name}>
                      {activeSop.name}
                    </span>
                    <span className="text-[10px] text-pg-ink-subtle mt-0.5">Total parsed items: {activeSop.steps.length}</span>
                  </div>
                  <button className="flex items-center gap-1.5 text-xs text-pg-primary font-semibold hover:underline cursor-pointer">
                    <DocumentArrowDown20Regular />
                    <span>Download JSON</span>
                  </button>
                </div>

                {/* Steps checklist list */}
                <div className="flex-grow overflow-y-auto pr-1 flex flex-col gap-2.5">
                  {activeSop.steps.map((step: any) => {
                    let typeBadge = 'bg-pg-semantic-success-bg text-pg-semantic-success';
                    if (step.checkType === 'sequence') typeBadge = 'bg-pg-primary-subtle text-pg-primary';
                    else if (step.checkType === 'fine_detail') typeBadge = 'bg-pg-semantic-review-bg text-pg-semantic-review';

                    return (
                      <div 
                        key={step.stepId}
                        className="p-2.5 bg-pg-surface-2 border border-pg-hairline rounded-pg-sm flex flex-col gap-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-[10px] font-bold text-pg-ink">
                            {step.stepId} (Seq: {step.sequence})
                          </span>
                          <span className={`text-[9px] font-bold px-1.5 py-0.2 rounded-full uppercase tracking-wider ${typeBadge}`}>
                            {step.checkType.replace('_', ' ')}
                          </span>
                        </div>
                        <div className="text-[11px] text-pg-ink-muted leading-relaxed font-sans">
                          {step.criterion}
                        </div>
                        <div className="text-[9px] text-pg-ink-subtle truncate">
                          Section: {step.section}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="flex-grow flex flex-col items-center justify-center text-center text-pg-ink-subtle p-6 gap-2">
                <DocumentBulletList20Regular className="w-8 h-8 text-pg-ink-subtle" />
                <div className="text-xs font-semibold">No SOP selected</div>
                <div className="text-[10px]">Select an SOP from the left column to view its parsed checklist structure.</div>
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Information Panel */}
      <div className="p-3 bg-pg-semantic-info-bg border-l-4 border-pg-semantic-info rounded-pg-md flex items-start gap-2.5 text-xs text-pg-ink">
        <Info20Regular className="text-pg-primary mt-0.5 flex-shrink-0" />
        <div className="flex flex-col gap-0.5">
          <span className="font-bold">Checklist Tiering & Verifiability Constraints</span>
          <span className="text-pg-ink-muted text-[11px] leading-relaxed">
            ProcedureGuard segments SOP steps by visual verifiability. <strong>Presence</strong> and <strong>Sequence</strong> checks can be resolved by overhead video analyzer agents. <strong>Fine-detail</strong> checks (torque specifications, seating clearance, rotation levels) route to manual verification because visual frame resolutions cannot reliably confirm compliance.
          </span>
        </div>
      </div>
    </div>
  );
}
