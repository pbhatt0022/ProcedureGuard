'use client';

import React from 'react';
import { useApp } from '../../lib/context';
import { Info20Regular } from '@fluentui/react-icons';

// Read-only settings/about view. ProcedureGuard's runtime config (perception mode,
// Azure endpoints, auth) is set via environment/CLI, not the UI — so this page
// surfaces current state honestly rather than faking interactive controls.
export default function SettingsPage() {
  const { allRuns } = useApp();

  const rows: { label: string; value: string }[] = [
    { label: 'Reviewer', value: 'Vikram Nair · QA Manager' },
    { label: 'Runs in store', value: String(allRuns.length) },
    { label: 'Run store', value: 'Local JSON (runs/<run_id>.json)' },
    { label: 'Perception', value: 'GPT-4o Vision (default) · IndustReal ASD when USE_ASD_PERCEPTION=true' },
    { label: 'Reasoning model', value: 'Azure OpenAI GPT-4o (Entra ID / DefaultAzureCredential)' },
    { label: 'Compliance standard', value: 'ISO 13485 · FDA 21 CFR Part 820' },
  ];

  return (
    <div className="p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full select-none">
      <section className="flex flex-col gap-1">
        <h1 className="text-xl font-semibold text-pg-ink">Settings</h1>
        <p className="text-xs text-pg-ink-muted leading-none">
          Current console configuration. Runtime settings are managed via environment variables and the pipeline CLI.
        </p>
      </section>

      <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md overflow-hidden shadow-pg-subtle">
        <table className="w-full text-left border-collapse text-xs">
          <tbody className="divide-y divide-pg-hairline">
            {rows.map(r => (
              <tr key={r.label}>
                <td className="px-4 py-3 w-56 font-bold text-pg-ink-muted uppercase tracking-wider text-[11px]">{r.label}</td>
                <td className="px-4 py-3 text-pg-ink font-mono">{r.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="p-3 bg-pg-semantic-info-bg border-l-4 border-pg-semantic-info rounded-pg-md flex items-start gap-2.5 text-xs text-pg-ink">
        <Info20Regular className="text-pg-primary mt-0.5 flex-shrink-0" />
        <span className="text-pg-ink-muted text-[11px] leading-relaxed">
          This is a demo console. Authentication, model endpoints, and the perception backend are configured in
          <span className="font-mono"> .env</span> / <span className="font-mono">.env.local</span> and via <span className="font-mono">az login</span>, not editable here.
        </span>
      </div>
    </div>
  );
}
