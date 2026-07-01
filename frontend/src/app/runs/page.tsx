'use client';

import React, { useState, useEffect, useRef, useMemo, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useApp } from '../../lib/context';
import { Verdict, DashboardRow } from '../../lib/types';
import { formatDuration, formatTimestamp, formatConfidence } from '../../lib/normalizer';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckmarkCircle20Regular,
  ErrorCircle20Regular,
  Warning20Regular,
  PersonFeedback20Regular,
  ArrowSync20Regular,
  Clock20Regular,
  Dismiss20Regular,
  Play20Regular,
  Pause20Regular,
  DocumentArrowDown20Regular,
  Share20Regular,
  ArrowCounterclockwise20Regular,
  Info20Regular,
  Send20Regular,
  Bot20Regular,
  Person20Regular,
  Alert20Regular,
  ArrowRight20Regular
} from '@fluentui/react-icons';

type TabId = 'OVERVIEW' | 'STEPS' | 'EVIDENCE' | 'REVIEW' | 'AUDIT' | 'ASK';

interface ChatMessage {
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
}

function RunsCockpit() {
  const {
    activeRunId,
    setActiveRunId,
    normalizedCtx,
    updateReviewerOverride,
    searchQuery,
    isLoading,
    error,
    allRuns
  } = useApp();

  const searchParams = useSearchParams();
  const router = useRouter();

  // Get active tab from URL query param
  const tabParam = searchParams.get('tab') as TabId;
  const initialTab: TabId = (tabParam && ['OVERVIEW', 'STEPS', 'EVIDENCE', 'REVIEW', 'AUDIT', 'ASK'].includes(tabParam)) 
    ? tabParam 
    : 'OVERVIEW';

  // Get filter from URL query param
  const filterParam = searchParams.get('filter');
  const initialFilter = filterParam || 'ALL';

  // Selected row state for keyboard and detail navigation
  const [selectedRowIndex, setSelectedRowIndex] = useState<number>(0);
  const [isDrawerOpen, setIsDrawerOpen] = useState<boolean>(false);
  
  // Tab spine state
  const [activeTab, setActiveTab] = useState<TabId>(initialTab);
  
  // Table visual states
  const [activeFilter, setActiveFilter] = useState<string>(initialFilter);
  const [sortField, setSortField] = useState<'sequence' | 'verdict' | 'confidence' | 'review_state'>('sequence');
  const [sortAsc, setSortAsc] = useState<boolean>(true);
  const [isCompactDensity, setIsCompactDensity] = useState<boolean>(true);

  // Sync the active run from the ?run= query param, so refresh/deep-link/bookmark
  // preserves which run is shown (otherwise it reverts to the default).
  useEffect(() => {
    const runParam = searchParams.get('run');
    if (runParam && runParam !== activeRunId && allRuns.some(r => r.id === runParam)) {
      setActiveRunId(runParam);
    }
  }, [searchParams, allRuns, activeRunId, setActiveRunId]);

  // Sync state from query parameters on navigation
  useEffect(() => {
    const tabParam = searchParams.get('tab') as TabId;
    if (tabParam && ['OVERVIEW', 'STEPS', 'EVIDENCE', 'REVIEW', 'AUDIT', 'ASK'].includes(tabParam)) {
      setActiveTab(tabParam);
    } else {
      setActiveTab('OVERVIEW');
    }
  }, [searchParams]);

  useEffect(() => {
    const filterParam = searchParams.get('filter');
    if (filterParam) {
      setActiveFilter(filterParam);
    } else {
      setActiveFilter('ALL');
    }
  }, [searchParams]);

  const handleTabChange = (newTab: TabId) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('tab', newTab);
    router.push(`/runs?${params.toString()}`, { scroll: false });
    setIsDrawerOpen(false);
  };

  const handleFilterChange = (newFilter: string) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set('filter', newFilter);
    router.push(`/runs?${params.toString()}`, { scroll: false });
  };

  // Video and timeline playback sync states
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<number>(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const timelineVideoRef = useRef<HTMLVideoElement>(null);
  const tableRef = useRef<HTMLDivElement>(null);

  // Ask tab chat states
  const [chatInput, setChatInput] = useState<string>('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      sender: 'agent',
      text: 'Hi, I\'m your Compliance Assistant. Ask me anything about this run — verdicts, deviations, inspection steps, tickets, or audit logs. Try "what steps have deviations?" or "show open tickets for this run".',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  // Get runs context rows (null-safe: hooks below must run on every render, even
  // while data is still loading — the early returns now live AFTER all hooks).
  const allRows = normalizedCtx?.rows ?? [];

  // Filter rows based on search query and active filter badge
  const filteredRows = useMemo(() => {
    let result = allRows;

    // Filter by search query (global search from command bar)
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      result = result.filter(row => 
        row.step_id.toLowerCase().includes(q) ||
        row.criterion.toLowerCase().includes(q) ||
        row.reasoning.toLowerCase().includes(q) ||
        row.section.toLowerCase().includes(q)
      );
    }

    // Filter by verdict card selection
    if (activeFilter !== 'ALL') {
      if (activeFilter === 'NEEDS_REVIEW') {
        result = result.filter(row => 
          row.verdict === 'Deviation Detected' ||
          row.verdict === 'Requires Inspection' ||
          row.verdict === 'Unable to Verify'
        );
      } else {
        result = result.filter(row => row.verdict === activeFilter);
      }
    }

    // Sort rows
    result = [...result].sort((a, b) => {
      let valA: any = a[sortField];
      let valB: any = b[sortField];

      // Handle null values
      if (valA === null || valA === undefined) valA = sortAsc ? 999999 : -999999;
      if (valB === null || valB === undefined) valB = sortAsc ? 999999 : -999999;

      if (typeof valA === 'string') {
        return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
      } else {
        return sortAsc ? valA - valB : valB - valA;
      }
    });

    return result;
  }, [allRows, searchQuery, activeFilter, sortField, sortAsc]);

  // Attention required checklist (only deviations, inspection, unable rows)
  const attentionShortlist = useMemo(() => {
    return allRows.filter(row => 
      row.verdict === 'Deviation Detected' ||
      row.verdict === 'Requires Inspection' ||
      row.verdict === 'Unable to Verify'
    );
  }, [allRows]);

  // Set selected index limits
  const activeSelectedRow = filteredRows[selectedRowIndex] || filteredRows[0] || null;

  // Sync index when filter changes
  useEffect(() => {
    setSelectedRowIndex(0);
  }, [activeFilter, searchQuery]);

  // Sync video timeupdate for evidence player
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, [activeSelectedRow, activeTab]);

  // Sync timeline video timeupdate
  useEffect(() => {
    const video = timelineVideoRef.current;
    if (!video) return;

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime);
    };

    const handlePlay = () => setIsPlaying(true);
    const handlePause = () => setIsPlaying(false);

    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('play', handlePlay);
    video.addEventListener('pause', handlePause);

    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('play', handlePlay);
      video.removeEventListener('pause', handlePause);
    };
  }, [activeTab]);

  // Handle keyboard navigation shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const activeEl = document.activeElement;
      const isInput = activeEl?.tagName === 'INPUT' || activeEl?.tagName === 'TEXTAREA';
      if (isInput) return; // Skip if typing

      if (filteredRows.length === 0) return;

      switch (e.key) {
        case 'j':
          // Move down
          setSelectedRowIndex(prev => Math.min(prev + 1, filteredRows.length - 1));
          e.preventDefault();
          break;
        case 'k':
          // Move up
          setSelectedRowIndex(prev => Math.max(prev - 1, 0));
          e.preventDefault();
          break;
        case 'Enter':
          // Open drawer
          if (activeTab === 'OVERVIEW' || activeTab === 'STEPS') {
            setIsDrawerOpen(true);
          }
          e.preventDefault();
          break;
        case 'Escape':
          // Close drawer
          setIsDrawerOpen(false);
          e.preventDefault();
          break;
        case 'c':
          // Mark compliant override
          if (activeSelectedRow) {
            updateReviewerOverride(activeSelectedRow.item_id, {
              verdict: 'Compliant',
              status: 'Confirmed compliant',
              notes: 'Confirmed compliant via reviewer keyboard action'
            });
          }
          break;
        case 'd':
          // Mark deviation override
          if (activeSelectedRow) {
            updateReviewerOverride(activeSelectedRow.item_id, {
              verdict: 'Deviation Detected',
              status: 'Confirmed deviation',
              notes: 'Confirmed deviation via reviewer keyboard action'
            });
          }
          break;
        case 'u':
          // Mark unable override
          if (activeSelectedRow) {
            updateReviewerOverride(activeSelectedRow.item_id, {
              verdict: 'Unable to Verify',
              status: 'Marked unable to verify',
              notes: 'Marked unable to verify via reviewer keyboard action'
            });
          }
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [filteredRows, activeSelectedRow, updateReviewerOverride, activeTab]);

  // ── Early returns (AFTER all hooks, so hook order is stable across renders) ──
  if (isLoading) {
    return (
      <div className="p-6 flex flex-col gap-4 animate-pulse max-w-7xl mx-auto w-full select-none">
        <div className="h-8 bg-pg-surface-3 rounded w-1/4" />
        <div className="h-4 bg-pg-surface-3 rounded w-1/3" />
        <div className="grid grid-cols-5 gap-3 mt-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-20 bg-pg-surface-3 rounded" />
          ))}
        </div>
        <div className="h-64 bg-pg-surface-3 rounded mt-4" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full select-none">
        <h1 className="text-xl font-semibold text-pg-ink">Error Loading Run</h1>
        <div className="p-4 bg-pg-semantic-error-bg border-l-4 border-pg-semantic-error rounded-pg-md text-xs text-pg-ink">
          <p className="font-bold">Failed to load run details:</p>
          <p className="mt-1 font-mono text-pg-ink-muted">{error}</p>
        </div>
      </div>
    );
  }

  if (allRuns.length === 0 || !normalizedCtx) {
    return (
      <div className="p-6 flex flex-col gap-6 max-w-7xl mx-auto w-full select-none">
        <h1 className="text-xl font-semibold text-pg-ink">Compliance Verification Cockpit</h1>
        <div className="p-8 bg-pg-canvas border border-pg-hairline rounded-pg-md text-center flex flex-col items-center justify-center gap-3">
          <p className="text-sm font-semibold text-pg-ink">No verification runs available</p>
          <p className="text-xs text-pg-ink-muted">To view reports, run the ProcedureGuard pipeline script to populate the run store.</p>
        </div>
      </div>
    );
  }

  // Seek video and play segment helper
  const seekVideoTo = (seconds: number) => {
    const video = activeTab === 'OVERVIEW' ? timelineVideoRef.current : videoRef.current;
    if (video) {
      video.currentTime = seconds;
      video.play().catch(() => {});
      setIsPlaying(true);
    }
  };

  const handleRowClick = (index: number) => {
    setSelectedRowIndex(index);
    setIsDrawerOpen(true);
  };

  const toggleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(true);
    }
  };

  // Chat Q&A agent handler
  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMsg: ChatMessage = {
      sender: 'user',
      text: chatInput,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setChatMessages(prev => [...prev, userMsg]);
    const query = chatInput;
    setChatInput('');

    // Add a temporary typing indicator message
    setChatMessages(prev => [...prev, {
      sender: 'agent',
      text: 'Thinking...',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isTyping: true
    } as any]);

    try {
      const res = await fetch(`/api/runs/${activeRunId}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question: query })
      });

      if (!res.ok) {
        throw new Error(`Chat API error: ${res.statusText}`);
      }

      const data = await res.json();
      
      // Replace typing indicator with real answer
      setChatMessages(prev => prev.filter(m => !(m as any).isTyping).concat({
        sender: 'agent',
        text: data.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }));
    } catch (err: any) {
      console.error('Failed to get answer:', err);
      // Replace typing indicator with error message
      setChatMessages(prev => prev.filter(m => !(m as any).isTyping).concat({
        sender: 'agent',
        text: `Error: ${err.message || 'Failed to connect to agent.'}`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }));
    }
  };

  const isWorkspaceClean = normalizedCtx.review_queue_count === 0;

  return (
    <div className="flex flex-col h-full overflow-hidden select-none">
      
      {/* Page Header (run details + actions) */}
      <section className="bg-pg-canvas border-b border-pg-hairline p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3">
            <h1 className="text-body-emphasis font-mono text-base font-semibold text-pg-ink">
              Run ID: {normalizedCtx.run_id}
            </h1>
            
            {/* Status Badge */}
            <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1.5 ${
              normalizedCtx.workspace_tone === 'critical' 
                ? 'bg-pg-semantic-error-bg text-pg-semantic-error' 
                : normalizedCtx.workspace_tone === 'review'
                  ? 'bg-pg-semantic-review-bg text-pg-semantic-review'
                  : 'bg-pg-semantic-success-bg text-pg-semantic-success'
            }`}>
              <span className={`w-1.5 h-1.5 rounded-full ${
                normalizedCtx.workspace_tone === 'critical' 
                  ? 'bg-pg-semantic-error' 
                  : normalizedCtx.workspace_tone === 'review'
                    ? 'bg-pg-semantic-review'
                    : 'bg-pg-semantic-success'
              }`} />
              {normalizedCtx.workspace_status}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-pg-ink-muted">
            <span className="font-medium">SOP: <span className="font-semibold">{normalizedCtx.sop_document}</span></span>
            <span className="text-pg-hairline-strong">|</span>
            <span>Video: <span className="font-mono">{normalizedCtx.video_name}</span></span>
            <span className="text-pg-hairline-strong">|</span>
            <span>Analyzed: <span>{normalizedCtx.created_at}</span></span>
          </div>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-2">
          <button
            disabled
            title="Re-runs are triggered from the pipeline CLI (e.g. python scripts/run_industreal_demo.py), not the dashboard."
            className="flex items-center gap-2 text-xs text-pg-ink-subtle font-semibold px-3 py-1.5 border border-pg-hairline rounded-pg-sm bg-pg-surface-2 cursor-not-allowed opacity-60"
          >
            <ArrowCounterclockwise20Regular className="text-pg-ink-subtle" />
            <span>Re-run pipeline</span>
          </button>
          <button
            onClick={() => handleTabChange('REVIEW')}
            title="Open the Human Review queue for this run"
            className="flex items-center gap-2 text-xs text-pg-ink font-semibold px-3 py-1.5 border border-pg-hairline-strong rounded-pg-sm bg-pg-canvas hover:bg-pg-surface-hover cursor-pointer btn-tactile"
          >
            <Share20Regular className="text-pg-ink-muted" />
            <span>Send for review</span>
          </button>
          <a
            href="/export"
            onClick={() => {
              if (!isWorkspaceClean) {
                alert("Note: this run has deviations or inspection items pending review. The exported report will be watermarked DRAFT.");
              }
            }}
            className="flex items-center gap-2 text-xs text-white font-semibold px-3 py-1.5 rounded-pg-sm bg-pg-primary hover:bg-pg-primary-hover cursor-pointer btn-tactile"
          >
            <DocumentArrowDown20Regular />
            <span>{isWorkspaceClean ? "Export Report" : "Export Draft"}</span>
          </a>
        </div>
      </section>

      {/* Verification Tabs spine headers */}
      <div className="bg-pg-canvas border-b border-pg-hairline px-4 flex gap-1 text-xs select-none">
        {(['OVERVIEW', 'STEPS', 'EVIDENCE', 'REVIEW', 'AUDIT', 'ASK'] as TabId[]).map(tab => {
          const isActive = activeTab === tab;
          return (
            <button
              key={tab}
              onClick={() => {
                handleTabChange(tab);
              }}
              className={`relative px-3.5 py-3 font-semibold transition-colors duration-150 cursor-pointer btn-tactile ${
                isActive ? 'text-pg-primary font-bold' : 'text-pg-ink-muted hover:text-pg-ink hover:bg-pg-surface-hover'
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="activeTabPill"
                  className="absolute inset-x-0 bottom-0 h-[2px] bg-pg-primary z-20"
                  transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                />
              )}
              {isActive && (
                <motion.div
                  layoutId="activeTabBg"
                  className="absolute inset-0 bg-pg-primary-subtle/50 rounded-t-pg-sm z-0"
                  transition={{ type: 'spring', stiffness: 380, damping: 32 }}
                />
              )}
              <span className="relative z-10 font-display">
                {tab === 'OVERVIEW' && 'Overview'}
                {tab === 'STEPS' && 'Step verification'}
                {tab === 'EVIDENCE' && 'Evidence workspace'}
                {tab === 'REVIEW' && 'Human review'}
                {tab === 'AUDIT' && 'Audit trail'}
                {tab === 'ASK' && 'Ask'}
              </span>
            </button>
          );
        })}
      </div>

      {/* Main Inner Content Body */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Render ACTIVE TAB View */}
        <div className="flex-1 overflow-y-auto p-4 flex flex-col min-w-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.15, ease: [0.23, 1, 0.32, 1] }}
              className="flex-grow flex flex-col gap-4"
            >
              
              {/* TAB 1: OVERVIEW */}
          {activeTab === 'OVERVIEW' && (
            <>
              {/* KPI Summary Row */}
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-3">
                <div className="p-3 bg-pg-primary-subtle/30 border border-pg-primary-border-subtle/40 rounded-pg-md text-left flex flex-col justify-between hover:shadow-pg-card transition-all">
                  <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Overall Adherence</span>
                  <div className="flex items-end justify-between mt-1">
                    <span className="text-2xl font-bold tabular-nums text-pg-ink font-display">{normalizedCtx.score_text}</span>
                    <svg className="w-8 h-8 flex-shrink-0" viewBox="0 0 36 36">
                      <path className="text-pg-hairline" strokeWidth="3.5" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      <path className="text-pg-primary" strokeWidth="3.5" strokeDasharray={`${normalizedCtx.score_pct || 0}, 100`} strokeLinecap="round" stroke="currentColor" fill="none" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    </svg>
                  </div>
                  <span className="text-[10px] text-pg-ink-subtle mt-1">{normalizedCtx.compliant} of {normalizedCtx.verifiable_total} verifiable steps</span>
                </div>
                
                <div className="p-3 bg-pg-semantic-success-bg/15 border border-pg-semantic-success/10 rounded-pg-md flex flex-col justify-between hover:shadow-pg-card transition-all">
                  <span className="text-[10px] font-bold text-pg-semantic-success uppercase tracking-wider">Compliant</span>
                  <span className="text-2xl font-bold tabular-nums text-pg-semantic-success mt-1 font-display">{normalizedCtx.compliant}</span>
                  <span className="text-[10px] text-pg-ink-subtle mt-1">Confirmed correct</span>
                </div>
                
                <div className="p-3 bg-pg-semantic-error-bg/15 border border-pg-semantic-error/10 rounded-pg-md flex flex-col justify-between hover:shadow-pg-card transition-all">
                  <span className="text-[10px] font-bold text-pg-semantic-error uppercase tracking-wider">Deviations</span>
                  <span className="text-2xl font-bold tabular-nums text-pg-semantic-error mt-1 font-display">{normalizedCtx.deviation}</span>
                  <span className="text-[10px] text-pg-ink-subtle mt-1">SOP violations</span>
                </div>

                <div className="p-3 bg-pg-semantic-warning-bg/15 border border-pg-semantic-warning/10 rounded-pg-md flex flex-col justify-between hover:shadow-pg-card transition-all">
                  <span className="text-[10px] font-bold text-pg-semantic-warning uppercase tracking-wider">Unable to Verify</span>
                  <span className="text-2xl font-bold tabular-nums text-pg-semantic-warning mt-1 font-display">{normalizedCtx.unable_to_verify}</span>
                  <span className="text-[10px] text-pg-ink-subtle mt-1">Camera coverage gaps</span>
                </div>

                <div className="p-3 bg-pg-semantic-review-bg/15 border border-pg-semantic-review/10 rounded-pg-md flex flex-col justify-between hover:shadow-pg-card transition-all">
                  <span className="text-[10px] font-bold text-pg-semantic-review uppercase tracking-wider">Requires Inspection</span>
                  <span className="text-2xl font-bold tabular-nums text-pg-semantic-review mt-1 font-display">{normalizedCtx.requires_inspection}</span>
                  <span className="text-[10px] text-pg-ink-subtle mt-1">Fine-detail checks</span>
                </div>
              </div>

              {/* Stack-bar and Timeline */}
              <div className="bg-pg-canvas border border-pg-hairline p-3 rounded-pg-md flex flex-col gap-2">
                <div className="flex justify-between items-center text-xs font-semibold text-pg-ink-muted">
                  <span>Verdict Proportion Stack-bar</span>
                </div>
                <div className="h-3 w-full rounded-pg-sm flex overflow-hidden bg-pg-surface-2">
                  <div style={{ width: `${(normalizedCtx.compliant / normalizedCtx.total) * 100}%` }} className="bg-pg-semantic-success" />
                  <div style={{ width: `${(normalizedCtx.deviation / normalizedCtx.total) * 100}%` }} className="bg-pg-semantic-error" />
                  <div style={{ width: `${(normalizedCtx.unable_to_verify / normalizedCtx.total) * 100}%` }} className="bg-pg-semantic-warning" />
                  <div style={{ width: `${(normalizedCtx.requires_inspection / normalizedCtx.total) * 100}%` }} className="bg-pg-semantic-review" />
                </div>
              </div>

              {/* Scrubber Timeline */}
              <div className="bg-pg-canvas border border-pg-hairline p-3 rounded-pg-md flex flex-col gap-2">
                <div className="flex justify-between items-center text-xs font-semibold text-pg-ink-muted">
                  <span>Deviation Timeline synced to playhead</span>
                  <span className="font-mono text-pg-primary">{formatDuration(currentTime)} / {normalizedCtx.duration_text}</span>
                </div>
                <div className="relative h-10 bg-pg-surface-2 rounded-pg-sm overflow-hidden border border-pg-hairline">
                  {allRows.map((row) => {
                    if (row.evidence_start === null) return null;
                    const percent = (row.evidence_start / normalizedCtx.duration) * 100;
                    let tickColor = 'bg-pg-semantic-success';
                    let tickHeight = 'h-full w-0.5 opacity-40';
                    let tickClass = 'success';
                    if (row.verdict === 'Deviation Detected') {
                      tickColor = 'bg-pg-semantic-error';
                      tickHeight = 'h-full w-1 z-10';
                      tickClass = 'error';
                    } else if (row.verdict === 'Requires Inspection') {
                      tickColor = 'bg-pg-semantic-review';
                      tickHeight = 'h-4/5 w-1 z-10';
                      tickClass = 'review';
                    } else if (row.verdict === 'Unable to Verify') {
                      tickColor = 'bg-pg-semantic-warning';
                      tickHeight = 'h-3/5 w-1 z-10';
                      tickClass = 'warning';
                    }
                    return (
                      <button
                        key={row.item_id}
                        onClick={() => {
                          const idx = allRows.findIndex(r => r.item_id === row.item_id);
                          setSelectedRowIndex(idx >= 0 ? idx : 0);
                          setIsDrawerOpen(true);
                          seekVideoTo(row.evidence_start || 0);
                        }}
                        style={{ left: `${percent}%` }}
                        className="absolute top-0 bottom-0 flex items-center justify-center -translate-x-1/2 cursor-pointer group z-20 timeline-tick-btn"
                        title={`Step ${row.step_id}: ${row.verdict}`}
                      >
                        <div className={`timeline-tick ${tickHeight} ${tickColor} ${tickClass} rounded-full`} />
                      </button>
                    );
                  })}
                  <div style={{ left: `${(currentTime / normalizedCtx.duration) * 100}%` }} className="absolute top-0 bottom-0 w-0.5 bg-pg-primary z-20 pointer-events-none">
                    <div className="absolute top-0 -translate-x-1/2 w-2 h-2 bg-pg-primary rounded-full" />
                  </div>
                  <div className="absolute inset-0 cursor-pointer z-0" onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    seekVideoTo((x / rect.width) * normalizedCtx.duration);
                  }} />
                </div>
                
                {/* Embed an invisible video element in Overview to hold player instance */}
                <video ref={timelineVideoRef} className="hidden" src={normalizedCtx.video_file || "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"} />
              </div>

              {/* Attention shortlist table */}
              <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md overflow-hidden flex flex-col">
                <div className="p-3 border-b border-pg-hairline bg-pg-surface-2 flex justify-between items-center text-xs font-bold text-pg-ink-muted">
                  <span>Attention Required Checklist Shortlist</span>
                  <span>({attentionShortlist.length} unresolved steps)</span>
                </div>
                <table className="w-full text-left border-collapse">
                  <thead className="bg-pg-surface-3 text-[10px] font-bold text-pg-ink-muted h-8 border-b border-pg-hairline">
                    <tr>
                      <th className="w-6 pl-3 pr-1 text-center" />
                      <th className="px-3 py-1 font-mono">Step</th>
                      <th className="px-3 py-1">SOP Criterion</th>
                      <th className="px-3 py-1 w-44">Verdict</th>
                      <th className="px-3 py-1 w-24">Confidence</th>
                      <th className="px-3 py-1 w-28">Reviewer Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-pg-hairline text-xs">
                    {attentionShortlist.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center py-6 text-pg-ink-muted bg-pg-surface-2 font-medium">
                          All steps auto-cleared Compliant. Run is ready for export!
                        </td>
                      </tr>
                    ) : (
                      attentionShortlist.map((row, index) => {
                        const isSelected = activeSelectedRow && row.item_id === activeSelectedRow.item_id;
                        let barColor = 'bg-pg-semantic-error';
                        let verdictBg = 'text-pg-semantic-error bg-pg-semantic-error-bg';
                        
                        if (row.verdict === 'Requires Inspection') {
                          barColor = 'bg-pg-semantic-review';
                          verdictBg = 'text-pg-semantic-review bg-pg-semantic-review-bg';
                        } else if (row.verdict === 'Unable to Verify') {
                          barColor = 'bg-pg-semantic-warning';
                          verdictBg = 'text-pg-semantic-warning bg-pg-semantic-warning-bg';
                        }

                        return (
                          <tr
                            key={row.item_id}
                            onClick={() => {
                              const idx = allRows.findIndex(r => r.item_id === row.item_id);
                              setSelectedRowIndex(idx);
                              setIsDrawerOpen(true);
                            }}
                            style={{ animationDelay: `${index * 12}ms` }}
                            className={`hover:bg-pg-surface-hover cursor-pointer h-9 transition-colors animate-row ${
                              isSelected ? 'bg-pg-primary-subtle' : ''
                            }`}
                          >
                            <td className="pl-3 pr-1 py-1 text-center">
                              <div className={`w-2 h-2 rounded-full mx-auto ${barColor}`} title={row.verdict} />
                            </td>
                            <td className="px-3 py-1 font-mono font-semibold">{row.step_id}</td>
                            <td className="px-3 py-1 truncate max-w-[280px] font-medium" title={row.criterion}>{row.criterion}</td>
                            <td className="px-3 py-1">
                              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full font-bold text-[9px] uppercase tracking-wider ${verdictBg}`}>
                                {row.verdict}
                              </span>
                            </td>
                            <td className="px-3 py-1 font-semibold text-pg-ink-muted">{formatConfidence(row.confidence)}</td>
                            <td className="px-3 py-1">
                              <span className="font-bold text-[10px] text-pg-semantic-review">{row.review_state}</span>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* TAB 2: STEP VERIFICATION LEDGER */}
          {activeTab === 'STEPS' && (
            <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md overflow-hidden flex flex-col">
              <div className="p-3 border-b border-pg-hairline flex flex-wrap items-center justify-between gap-3 bg-pg-surface-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-pg-ink-muted">SOP Step Checklist DetailsList</span>
                  <span className="text-xs text-pg-ink-subtle">({filteredRows.length} steps shown)</span>
                </div>

                <div className="flex items-center gap-3">
                  {/* Verdict Filter Pill */}
                  <select 
                    value={activeFilter}
                    onChange={e => handleFilterChange(e.target.value)}
                    className="text-xs bg-pg-canvas border border-pg-hairline-strong rounded-pg-sm px-2 py-1 text-pg-ink outline-none"
                  >
                    <option value="ALL">Show all verdicts</option>
                    <option value="Compliant">Compliant</option>
                    <option value="Deviation Detected">Deviation Detected</option>
                    <option value="Unable to Verify">Unable to Verify</option>
                    <option value="Requires Inspection">Requires Inspection</option>
                    <option value="NEEDS_REVIEW">Backlog review required</option>
                  </select>

                  <button
                    onClick={() => setIsCompactDensity(!isCompactDensity)}
                    className="text-xs text-pg-ink px-2.5 py-1 border border-pg-hairline-strong bg-pg-canvas hover:bg-pg-surface-hover rounded-pg-sm font-semibold cursor-pointer btn-tactile"
                  >
                    {isCompactDensity ? 'Comfortable view' : 'Compact view'}
                  </button>
                </div>
              </div>

              {/* Table rendering */}
              <div ref={tableRef} className="overflow-x-auto max-h-[500px]">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-pg-surface-2 border-b border-pg-hairline sticky top-0 text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider z-10 font-display">
                    <tr className="h-9">
                      <th className="w-6 pl-3 pr-1 text-center" />
                      <th onClick={() => toggleSort('sequence')} className="px-3 py-1 cursor-pointer hover:bg-pg-surface-hover font-mono">Step</th>
                      <th className="px-3 py-1">SOP Requirement</th>
                      <th className="px-3 py-1 w-24">Type</th>
                      <th onClick={() => toggleSort('verdict')} className="px-3 py-1 w-44 cursor-pointer hover:bg-pg-surface-hover">Verdict</th>
                      <th onClick={() => toggleSort('confidence')} className="px-3 py-1 w-24 cursor-pointer hover:bg-pg-surface-hover">Conf.</th>
                      <th className="px-3 py-1 w-20">Time</th>
                      <th onClick={() => toggleSort('review_state')} className="px-3 py-1 w-32 cursor-pointer hover:bg-pg-surface-hover">Review State</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-pg-hairline text-xs">
                    {filteredRows.length === 0 ? (
                      <tr>
                        <td colSpan={8} className="text-center py-8 text-pg-ink-muted font-medium bg-pg-surface-2">
                          No steps match this filter or search query.
                        </td>
                      </tr>
                    ) : (
                      filteredRows.map((row, index) => {
                        const isSelected = activeSelectedRow && row.item_id === activeSelectedRow.item_id;
                        let barColor = 'bg-pg-semantic-success';
                        let verdictColor = 'text-pg-semantic-success bg-pg-semantic-success-bg';
                        
                        if (row.verdict === 'Deviation Detected') {
                          barColor = 'bg-pg-semantic-error';
                          verdictColor = 'text-pg-semantic-error bg-pg-semantic-error-bg';
                        } else if (row.verdict === 'Requires Inspection') {
                          barColor = 'bg-pg-semantic-review';
                          verdictColor = 'text-pg-semantic-review bg-pg-semantic-review-bg';
                        } else if (row.verdict === 'Unable to Verify') {
                          barColor = 'bg-pg-semantic-warning';
                          verdictColor = 'text-pg-semantic-warning bg-pg-semantic-warning-bg';
                        }

                        return (
                          <tr
                            key={row.item_id}
                            onClick={() => handleRowClick(index)}
                            style={{ animationDelay: `${index * 12}ms` }}
                            className={`cursor-pointer transition-all animate-row ${
                              isSelected ? 'bg-pg-primary-subtle' : 'hover:bg-pg-surface-hover'
                            } ${isCompactDensity ? 'h-9' : 'h-11'}`}
                          >
                            <td className="pl-3 pr-1 py-1 text-center">
                              <div className={`w-2 h-2 rounded-full mx-auto ${barColor}`} title={row.verdict} />
                            </td>
                            <td className="px-3 py-1 font-mono font-semibold">{row.step_id}</td>
                            <td className="px-3 py-1 max-w-[280px]">
                              <div className="line-clamp-1 font-medium text-pg-ink" title={row.criterion}>
                                {row.criterion}
                              </div>
                            </td>
                            <td className="px-3 py-1 font-mono text-pg-ink-muted capitalize">{row.check_type || 'presence'}</td>
                            <td className="px-3 py-1">
                              <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[9px] uppercase tracking-wider ${verdictColor}`}>
                                <span>{row.verdict}</span>
                              </span>
                            </td>
                            <td className="px-3 py-1">
                              <div className="flex flex-col gap-0.5 w-16">
                                <span className="font-semibold font-mono text-[10px] text-pg-ink">{formatConfidence(row.confidence)}</span>
                                {row.confidence_pct !== null && (
                                  <div className="h-[3px] w-full bg-pg-surface-3 rounded-full overflow-hidden">
                                    <div style={{ width: `${row.confidence_pct}%` }} className={`h-full ${row.confidence_pct >= 85 ? 'bg-pg-score-high' : 'bg-pg-score-medium'}`} />
                                  </div>
                                )}
                              </div>
                            </td>
                            <td className="px-3 py-1 font-mono text-[10px]">{row.evidence_start !== null ? formatDuration(row.evidence_start) : '-'}</td>
                            <td className="px-3 py-1">
                              <span className={`inline-block px-1.5 py-0.5 rounded-pg-sm text-[9px] font-bold ${
                                row.review_tone === 'success' ? 'bg-pg-semantic-success-bg text-pg-semantic-success' : 'bg-pg-semantic-review-bg text-pg-semantic-review'
                              }`}>{row.review_state}</span>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 3: EVIDENCE WORKSPACE */}
          {activeTab === 'EVIDENCE' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              
              {/* Left Column: Video Scrubber Player */}
              <div className="flex flex-col gap-3">
                <h3 className="text-xs font-bold text-pg-ink-muted uppercase tracking-wider">Visual Evidence Playback</h3>
                <div className="relative border border-pg-hairline rounded-pg-md overflow-hidden bg-pg-inverse-canvas aspect-video">
                  <video
                    ref={videoRef}
                    className="w-full h-full object-contain"
                    controls
                    playsInline
                    src={normalizedCtx.video_file || "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"}
                  />
                  <div className="absolute top-2 left-2 px-1.5 py-0.5 bg-black/60 text-white font-mono text-[9px] uppercase tracking-wide rounded-pg-xs pointer-events-none select-none z-10">
                    CAM-OVERHEAD-01
                  </div>
                </div>
                
                {/* Active seek controllers */}
                {activeSelectedRow && activeSelectedRow.evidence_start !== null && (
                  <button
                    onClick={() => seekVideoTo(activeSelectedRow.evidence_start || 0)}
                    className="text-xs text-white bg-pg-primary font-semibold py-2 px-3 rounded-pg-sm hover:bg-pg-primary-hover flex items-center justify-center gap-1 cursor-pointer btn-tactile"
                  >
                    <Clock20Regular />
                    <span>Seek Player to Segment ({formatTimestamp(activeSelectedRow.evidence_start, activeSelectedRow.evidence_end)})</span>
                  </button>
                )}
              </div>

              {/* Right Column: Step Evidence Details */}
              <div className="flex flex-col gap-4 bg-pg-canvas border border-pg-hairline p-4 rounded-pg-md shadow-pg-subtle">
                {activeSelectedRow ? (
                  <>
                    <div className="flex items-center justify-between border-b border-pg-hairline pb-2">
                      <span className="text-xs font-bold text-pg-ink">Step: {activeSelectedRow.step_id} ({activeSelectedRow.item_id})</span>
                      <span className={`px-2.5 py-0.5 rounded-full font-bold text-[9px] uppercase tracking-wider ${
                        activeSelectedRow.verdict === 'Compliant' ? 'bg-pg-semantic-success-bg text-pg-semantic-success' : 'bg-pg-semantic-error-bg text-pg-semantic-error'
                      }`}>{activeSelectedRow.verdict}</span>
                    </div>

                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">SOP Document excerpt</span>
                      <div className="p-3 bg-pg-surface-2 rounded-pg-sm border border-pg-hairline text-xs font-medium text-pg-ink italic">
                        "{activeSelectedRow.criterion}"
                      </div>
                    </div>

                    <div className="flex flex-col gap-1">
                      <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">GPT reasoning summary</span>
                      <div className="p-3 border border-pg-hairline bg-pg-canvas text-xs leading-relaxed text-pg-ink rounded-pg-md">
                        {activeSelectedRow.reasoning}
                      </div>
                    </div>

                    <div className="flex flex-col gap-1 mt-2">
                      <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Metadata variables</span>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="p-2 bg-pg-surface-2 rounded border border-pg-hairline flex flex-col">
                          <span className="text-[9px] text-pg-ink-muted uppercase tracking-wider">Confidence</span>
                          <span className="font-bold font-mono">{formatConfidence(activeSelectedRow.confidence)}</span>
                        </div>
                        <div className="p-2 bg-pg-surface-2 rounded border border-pg-hairline flex flex-col">
                          <span className="text-[9px] text-pg-ink-muted uppercase tracking-wider">Evidence range</span>
                          <span className="font-bold font-mono">{activeSelectedRow.evidence_window}</span>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="flex-grow flex flex-col items-center justify-center text-center p-6 text-pg-ink-subtle gap-2">
                    <Info20Regular className="w-8 h-8 text-pg-ink-subtle" />
                    <div className="text-xs font-semibold">No step selected</div>
                    <div className="text-[10px]">Select a step row from the Step Verification tab to view matching evidence details here.</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 4: HUMAN REVIEW SESSION */}
          {activeTab === 'REVIEW' && (
            <div className="flex flex-col md:flex-row gap-4 overflow-hidden h-[500px]">
              
              {/* Backlog List */}
              <div className="flex-1 bg-pg-canvas border border-pg-hairline rounded-pg-md overflow-y-auto shadow-pg-subtle">
                <div className="p-3 border-b border-pg-hairline bg-pg-surface-2 text-xs font-bold text-pg-ink-muted">
                  Run Backlog Queue ({attentionShortlist.length} items)
                </div>
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-pg-hairline h-8 bg-pg-surface-3 text-[10px] font-bold uppercase tracking-wider text-pg-ink-muted">
                      <th className="w-6 pl-3 pr-1 text-center" />
                      <th className="px-3 py-1 font-mono">Step</th>
                      <th className="px-3 py-1">Criterion</th>
                      <th className="px-3 py-1 w-36">Verdict</th>
                    </tr>
                  </thead>
                  <tbody>
                    {attentionShortlist.map((row) => {
                      const isSelected = activeSelectedRow && row.item_id === activeSelectedRow.item_id;
                      let barColor = 'bg-pg-semantic-error';
                      if (row.verdict === 'Requires Inspection') barColor = 'bg-pg-semantic-review';
                      else if (row.verdict === 'Unable to Verify') barColor = 'bg-pg-semantic-warning';

                      return (
                        <tr
                          key={row.item_id}
                          onClick={() => {
                            const idx = allRows.findIndex(r => r.item_id === row.item_id);
                            setSelectedRowIndex(idx);
                          }}
                          className={`hover:bg-pg-surface-hover cursor-pointer h-9 transition-colors ${
                            isSelected ? 'bg-pg-primary-subtle' : ''
                          }`}
                        >
                          <td className="pl-3 pr-1 py-1 text-center">
                            <div className={`w-2 h-2 rounded-full mx-auto ${barColor}`} title={row.verdict} />
                          </td>
                          <td className="px-3 py-1 font-mono font-semibold">{row.step_id}</td>
                          <td className="px-3 py-1 truncate max-w-[150px] font-medium">{row.criterion}</td>
                          <td className="px-3 py-1">
                            <span className="font-bold text-[10px] text-pg-ink-muted">{row.verdict}</span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Overrides and note editor */}
              <div className="w-full md:w-[380px] bg-pg-canvas border border-pg-hairline rounded-pg-md p-4 flex flex-col gap-4 shadow-pg-subtle overflow-y-auto">
                {activeSelectedRow ? (
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col border-b border-pg-hairline pb-2">
                      <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider font-mono">Supervisor Review</span>
                      <span className="text-xs font-bold text-pg-ink">{activeSelectedRow.step_id}</span>
                      <span className="text-[10px] text-pg-ink-subtle mt-0.5">Current state: {activeSelectedRow.verdict}</span>
                    </div>

                    <div className="flex flex-col gap-1.5">
                      <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">SOP Excerpt</span>
                      <p className="text-xs font-medium bg-pg-surface-2 p-2.5 rounded border border-pg-hairline text-pg-ink italic">
                        "{activeSelectedRow.criterion}"
                      </p>
                    </div>

                    <div className="flex flex-col gap-2 pt-2 border-t border-pg-hairline">
                      <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Decide Outcome</span>
                      
                      <button
                        onClick={() => updateReviewerOverride(activeSelectedRow.item_id, {
                          verdict: 'Compliant',
                          status: 'Confirmed compliant',
                          notes: 'Confirmed compliant visually by QA Manager'
                        })}
                        className="w-full text-center text-xs font-semibold py-2 rounded-pg-sm border border-pg-semantic-success text-pg-semantic-success bg-pg-semantic-success-bg hover:bg-pg-semantic-success hover:text-white cursor-pointer btn-tactile"
                      >
                        Confirm Compliant
                      </button>

                      <button
                        onClick={() => updateReviewerOverride(activeSelectedRow.item_id, {
                          verdict: 'Deviation Detected',
                          status: 'Confirmed deviation',
                          notes: 'Confirmed deviation visually by QA Manager'
                        })}
                        className="w-full text-center text-xs font-semibold py-2 rounded-pg-sm border border-pg-semantic-error text-pg-semantic-error bg-pg-semantic-error-bg hover:bg-pg-semantic-error hover:text-white cursor-pointer btn-tactile"
                      >
                        Confirm Deviation
                      </button>

                      <button
                        onClick={() => updateReviewerOverride(activeSelectedRow.item_id, {
                          verdict: 'Unable to Verify',
                          status: 'Marked unable to verify',
                          notes: 'Accepted as coverage gap'
                        })}
                        className="w-full text-center text-xs font-semibold py-2 rounded-pg-sm border border-pg-hairline-strong bg-pg-canvas hover:bg-pg-surface-hover text-pg-ink cursor-pointer btn-tactile"
                      >
                        Mark Unable to Verify
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center text-center text-pg-ink-subtle p-6">
                    <Info20Regular className="w-8 h-8 text-pg-ink-subtle mb-1" />
                    <span className="text-xs font-semibold">Select backlog row</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 5: AUDIT TRAIL */}
          {activeTab === 'AUDIT' && (
            <div className="relative pl-6 flex flex-col gap-4 border-l-2 border-pg-hairline py-2 max-h-[500px] overflow-y-auto">
              {normalizedCtx.audit_events.map((event, index) => (
                <div key={`${event.timestamp}-${index}`} className="relative group">
                  <div className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-2 border-pg-canvas flex items-center justify-center bg-pg-primary`} />
                  <div className="p-3 bg-pg-canvas border border-pg-hairline rounded-pg-md shadow-pg-subtle flex flex-col gap-1">
                    <div className="flex items-center justify-between text-[11px] font-bold text-pg-ink">
                      <span>{event.actor} · {event.title}</span>
                      <span className="font-mono text-[9px] text-pg-ink-subtle">{event.timestamp}</span>
                    </div>
                    <p className="text-[11px] text-pg-ink-muted leading-relaxed select-text">{event.body}</p>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* TAB 6: ASK (Q&A CHAT AGENT) */}
          {activeTab === 'ASK' && (
            <div className="bg-pg-canvas border border-pg-hairline rounded-pg-md shadow-pg-subtle flex flex-col h-[500px]">
              <div className="p-3 border-b border-pg-hairline bg-pg-surface-2 flex items-center gap-2 text-xs font-bold text-pg-ink-muted">
                <Bot20Regular className="text-pg-primary" />
                <span>Compliance Assistant</span>
              </div>

              {/* Chat Feed */}
              <div className="flex-grow overflow-y-auto p-4 flex flex-col gap-4">
                {chatMessages.map((msg, index) => {
                  const isAgent = msg.sender === 'agent';
                  return (
                    <div 
                      key={index} 
                      className={`flex gap-3 max-w-[85%] select-text ${
                        isAgent ? 'self-start' : 'self-end flex-row-reverse'
                      }`}
                    >
                      {/* Avatar */}
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold ${
                        isAgent ? 'bg-pg-primary-subtle text-pg-primary border border-pg-primary-border-subtle' : 'bg-pg-primary text-white'
                      }`}>
                        {isAgent ? <Bot20Regular /> : <Person20Regular />}
                      </div>

                      <div className={`p-3 rounded-pg-md border text-xs flex flex-col gap-1 leading-relaxed ${
                        isAgent 
                          ? 'bg-pg-surface-2 border-pg-hairline text-pg-ink' 
                          : 'bg-pg-primary text-white border-transparent'
                      }`}>
                        <div className="font-sans whitespace-pre-wrap select-text">{msg.text}</div>
                        <span className={`text-[9px] self-end mt-0.5 ${
                          isAgent ? 'text-pg-ink-subtle' : 'text-white/60 font-mono'
                        }`}>
                          {msg.timestamp}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Chat input form */}
              <form onSubmit={handleSendChat} className="p-3 border-t border-pg-hairline flex gap-2 bg-pg-surface-2">
                <input
                  type="text"
                  placeholder="Ask a question (e.g. 'what is the adherence score?')"
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  className="flex-grow px-3 py-1.5 text-xs bg-pg-canvas border border-pg-hairline-strong rounded-pg-sm focus:border-pg-primary focus:outline-none text-pg-ink font-sans"
                />
                <button
                  type="submit"
                  className="p-2 bg-pg-primary hover:bg-pg-primary-hover text-white rounded-pg-sm flex items-center justify-center cursor-pointer btn-tactile"
                  title="Send message"
                >
                  <Send20Regular />
                </button>
              </form>
            </div>
          )}

            </motion.div>
          </AnimatePresence>
        </div>

        <AnimatePresence>
          {isDrawerOpen && activeSelectedRow && (activeTab === 'OVERVIEW' || activeTab === 'STEPS') && (
            <motion.aside
              initial={{ transform: 'translateX(100%)' }}
              animate={{ transform: 'translateX(0%)' }}
              exit={{ transform: 'translateX(100%)' }}
              transition={{ type: 'spring', duration: 0.45, bounce: 0.15 }}
              className="w-full md:w-[480px] bg-pg-canvas border-l border-pg-hairline flex flex-col z-30 overflow-y-auto shadow-pg-dialog"
            >
              
              {/* Drawer Header */}
              <div className="p-4 border-b border-pg-hairline flex items-center justify-between bg-pg-surface-2 sticky top-0 z-10">
                <div className="flex flex-col gap-0.5">
                  <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider font-mono">Evidence package</span>
                  <span className="text-sm font-bold text-pg-ink">Step: {activeSelectedRow.step_id} ({activeSelectedRow.item_id})</span>
                </div>
                <button
                  onClick={() => setIsDrawerOpen(false)}
                  className="p-1 rounded-pg-sm hover:bg-pg-surface-hover text-pg-ink-subtle cursor-pointer btn-tactile"
                >
                  <Dismiss20Regular />
                </button>
              </div>

              {/* Drawer Body */}
              <div className="p-4 flex flex-col gap-5">
                
                {/* Verdict Details */}
                <div className="flex flex-col gap-2">
                  <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Model Verdict</span>
                  <div className="flex flex-wrap items-center justify-between p-3 border border-pg-hairline bg-pg-surface-2 rounded-pg-md gap-3">
                    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-bold text-xs ${
                      activeSelectedRow.verdict === 'Compliant'
                        ? 'text-pg-semantic-success bg-pg-semantic-success-bg'
                        : activeSelectedRow.verdict === 'Deviation Detected'
                          ? 'text-pg-semantic-error bg-pg-semantic-error-bg'
                          : activeSelectedRow.verdict === 'Unable to Verify'
                            ? 'text-pg-semantic-warning bg-pg-semantic-warning-bg'
                            : 'text-pg-semantic-review bg-pg-semantic-review-bg'
                    }`}>
                      {activeSelectedRow.verdict}
                    </span>
                    
                    <div className="flex flex-col gap-0.5 items-end">
                      <span className="text-xs font-bold text-pg-ink">
                        Confidence: {formatConfidence(activeSelectedRow.confidence)}
                      </span>
                      {activeSelectedRow.confidence_pct !== null && (
                        <div className="h-1.5 w-24 bg-pg-surface-3 rounded-full overflow-hidden">
                          <div style={{ width: `${activeSelectedRow.confidence_pct}%` }} className={`h-full ${activeSelectedRow.confidence_pct >= 85 ? 'bg-pg-score-high' : 'bg-pg-score-medium'}`} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Evidence Keyframe */}
                {activeSelectedRow.keyframe_blob_path && (
                  <div className="flex flex-col gap-2">
                    <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Evidence keyframe</span>
                    <div className="relative border border-pg-hairline rounded-pg-md overflow-hidden bg-pg-inverse-canvas aspect-video flex items-center justify-center">
                      <img
                        src={`/api/runs/${activeRunId}/keyframes/${activeSelectedRow.step_id}`}
                        alt={`Evidence frame for step ${activeSelectedRow.step_id}`}
                        className="w-full h-full object-contain"
                      />
                    </div>
                  </div>
                )}

                {/* Video Player */}
                <div className="flex flex-col gap-2">
                  <div className="flex justify-between items-center">
                    <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Video segment</span>
                    {activeSelectedRow.evidence_start !== null && (
                      <button 
                        onClick={() => seekVideoTo(activeSelectedRow.evidence_start || 0)}
                        className="text-xs text-pg-primary font-semibold hover:underline flex items-center gap-1 cursor-pointer btn-tactile"
                      >
                        <Clock20Regular className="w-4 h-4" />
                        <span>Seek to {formatTimestamp(activeSelectedRow.evidence_start, activeSelectedRow.evidence_end)}</span>
                      </button>
                    )}
                  </div>

                  <div className="relative border border-pg-hairline rounded-pg-md overflow-hidden bg-pg-inverse-canvas aspect-video">
                    <video
                      ref={videoRef}
                      className="w-full h-full object-contain"
                      controls
                      playsInline
                      src={normalizedCtx.video_file || "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"}
                    />
                    <div className="absolute top-2 left-2 px-1.5 py-0.5 bg-black/60 text-white font-mono text-[9px] uppercase tracking-wide rounded-pg-xs pointer-events-none select-none z-10">
                      CAM-OVERHEAD-01
                    </div>
                  </div>
                </div>

                {/* SOP Excerpt */}
                <div className="flex flex-col gap-2">
                  <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">SOP Requirement</span>
                  <div className="p-3 border-l-4 border-pg-hairline-strong bg-pg-surface-2 text-xs text-pg-ink leading-relaxed font-sans italic rounded-r-pg-md">
                    "{activeSelectedRow.criterion}"
                  </div>
                </div>

                {/* Reasoning Summary */}
                <div className="flex flex-col gap-2">
                  <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Reasoning Summary</span>
                  <div className="p-3 border border-pg-hairline bg-pg-canvas text-xs text-pg-ink leading-relaxed font-sans rounded-pg-md shadow-pg-subtle">
                    {activeSelectedRow.reasoning}
                  </div>
                </div>

                {/* Reviewer controls */}
                <div className="flex flex-col gap-2 pt-4 border-t border-pg-hairline">
                  <span className="text-[10px] font-bold text-pg-ink-muted uppercase tracking-wider">Reviewer Action</span>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => updateReviewerOverride(activeSelectedRow.item_id, {
                        verdict: 'Compliant',
                        status: 'Confirmed compliant',
                        notes: 'Confirmed compliant visually by QA Manager'
                      })}
                      className={`flex-1 text-xs font-semibold py-1.5 px-3 rounded-pg-sm border transition-all cursor-pointer btn-tactile ${
                        activeSelectedRow.review_state === 'Confirmed compliant'
                          ? 'bg-pg-semantic-success text-white border-transparent'
                          : 'bg-pg-canvas hover:bg-pg-surface-hover text-pg-ink border-pg-hairline-strong'
                      }`}
                    >
                      Confirm Compliant
                    </button>

                    <button
                      onClick={() => updateReviewerOverride(activeSelectedRow.item_id, {
                        verdict: 'Deviation Detected',
                        status: 'Confirmed deviation',
                        notes: 'Confirmed deviation visually by QA Manager'
                      })}
                      className={`flex-1 text-xs font-semibold py-1.5 px-3 rounded-pg-sm border transition-all cursor-pointer btn-tactile ${
                        activeSelectedRow.review_state === 'Confirmed deviation'
                          ? 'bg-pg-semantic-error text-white border-transparent'
                          : 'bg-pg-canvas hover:bg-pg-surface-hover text-pg-ink border-pg-hairline-strong'
                      }`}
                    >
                      Confirm Deviation
                    </button>
                  </div>

                  <div className="flex flex-col gap-1 mt-1">
                    <label htmlFor="drawer-notes-box" className="text-xs font-semibold text-pg-ink-muted">Reviewer Notes</label>
                    <textarea
                      id="drawer-notes-box"
                      placeholder="Enter notes for audit trail..."
                      rows={2}
                      value={activeSelectedRow.reasoning.includes('(Reviewer note)') ? activeSelectedRow.reasoning.split('(Reviewer note)')[0].trim() : ''}
                      onChange={(e) => updateReviewerOverride(activeSelectedRow.item_id, {
                        notes: e.target.value
                      })}
                      className="p-2 text-xs bg-pg-canvas border border-pg-hairline-strong rounded-pg-sm focus:border-pg-primary focus:outline-none w-full font-sans text-pg-ink"
                    />
                  </div>
                </div>
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default function RunsPage() {
  return (
    <Suspense fallback={
      <div className="p-6 flex flex-col gap-4 animate-pulse max-w-7xl mx-auto w-full select-none">
        <div className="h-8 bg-pg-surface-3 rounded w-1/4" />
        <div className="h-4 bg-pg-surface-3 rounded w-1/3" />
        <div className="grid grid-cols-5 gap-3 mt-4">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-20 bg-pg-surface-3 rounded" />
          ))}
        </div>
        <div className="h-64 bg-pg-surface-3 rounded mt-4" />
      </div>
    }>
      <RunsCockpit />
    </Suspense>
  );
}
