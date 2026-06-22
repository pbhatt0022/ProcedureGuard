'use client';

import React, { useState, Suspense } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { usePathname, useSearchParams } from 'next/navigation';
import { useApp } from '../lib/context';
import {
  Board20Regular,
  TableSimple20Regular,
  DocumentBulletList20Regular,
  Video20Regular,
  Alert20Regular,
  PersonFeedback20Regular,
  History20Regular,
  DocumentArrowDown20Regular,
  Settings20Regular,
  Search20Regular,
  ChevronLeft20Regular,
  ChevronRight20Regular,
  Person20Regular,
  QuestionCircle20Regular,
  Play20Filled,
  DocumentCheckmark24Filled
} from '@fluentui/react-icons';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  badgeKey?: 'review_queue_count' | 'deviation' | 'requires_inspection';
}

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const {
    activeRunId,
    allRuns,
    normalizedCtx,
    isNavCollapsed,
    setIsNavCollapsed,
    searchQuery,
    setSearchQuery
  } = useApp();

  // Navigation items consolidated into SidebarNavItems component below

  const getBadgeValue = (key?: NavItem['badgeKey']) => {
    if (!key || !normalizedCtx) return 0;
    if (key === 'review_queue_count') return normalizedCtx.review_queue_count;
    if (key === 'deviation') return normalizedCtx.deviation;
    if (key === 'requires_inspection') return normalizedCtx.requires_inspection;
    return 0;
  };

  return (
    <div className="flex flex-col min-h-screen bg-pg-app-background text-pg-ink">
      
      {/* Top Command Bar (48px) */}
      <header className="h-12 bg-pg-canvas border-b border-pg-hairline flex items-center justify-between px-4 z-40 select-none shadow-pg-subtle sticky top-0">
        <div className="flex items-center gap-6">
          
          {/* Logo & Identity */}
          <Link href="/" className="flex items-center gap-2 text-pg-primary font-semibold text-body-emphasis">
            <DocumentCheckmark24Filled className="text-pg-primary" />
            <span className="font-display">ProcedureGuard</span>
          </Link>
        </div>

        {/* Global Search & Actions */}
        <div className="flex items-center gap-3">
          
          {/* Global Search Box */}
          <div className="relative flex items-center">
            <Search20Regular className="absolute left-2.5 text-pg-ink-subtle" />
            <input
              type="text"
              placeholder="Search steps, criteria or reasoning..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="pl-8 pr-3 py-1 text-xs bg-pg-surface-2 hover:bg-pg-surface-3 focus:bg-pg-canvas border border-transparent focus:border-pg-primary rounded-pg-sm w-64 outline-none font-sans text-pg-ink transition-all"
            />
          </div>

          <div className="h-4 w-px bg-pg-hairline" />

          {/* Quick Info & Help */}
          <button 
            title="Help documentation" 
            className="p-1 rounded-pg-sm hover:bg-pg-surface-hover text-pg-ink-muted cursor-pointer active:scale-95 transition-all"
          >
            <QuestionCircle20Regular />
          </button>

          {/* Profile Badge */}
          <div className="flex items-center gap-2 pl-2">
            <div className="w-6 h-6 rounded-full bg-pg-primary text-white flex items-center justify-center text-xs font-semibold">
              VN
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-xs font-semibold text-pg-ink">Vikram Nair</span>
              <span className="text-[10px] text-pg-ink-muted">QA Manager</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content Layout */}
      <div className="flex flex-1 relative overflow-hidden">
        
        {/* Left Navigation Panel */}
        <nav 
          className={`bg-pg-canvas border-r border-pg-hairline flex flex-col justify-between transition-all duration-200 select-none z-30 sticky left-0`}
          style={{ width: isNavCollapsed ? '56px' : '240px' }}
        >
          {/* Nav Items */}
          <Suspense fallback={
            <div className="flex flex-col gap-2 p-2">
              {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
                <div key={i} className="h-8 bg-pg-surface-2 rounded animate-pulse" />
              ))}
            </div>
          }>
            <SidebarNavItems
              isNavCollapsed={isNavCollapsed}
              pathname={pathname}
              getBadgeValue={getBadgeValue}
            />
          </Suspense>

          {/* Bottom Settings & Toggle */}
          <div className="p-2 border-t border-pg-hairline flex flex-col gap-0.5">
            
            {/* Settings */}
            <Link
              href="/settings"
              className={`flex items-center gap-3 px-2.5 py-2 rounded-pg-sm text-pg-ink-muted hover:bg-pg-surface-hover hover:text-pg-ink transition-colors relative group btn-tactile ${
                pathname === '/settings' ? 'bg-pg-primary-subtle text-pg-primary font-semibold border-l-2 border-pg-primary' : ''
              }`}
            >
              <Settings20Regular className="w-5 h-5 flex-shrink-0" />
              {!isNavCollapsed && <span className="text-xs tracking-wide">Settings</span>}
              {isNavCollapsed && (
                <div className="absolute left-14 bg-pg-inverse-canvas text-pg-inverse-ink text-[11px] px-2.5 py-1 rounded-pg-sm opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 font-sans shadow-pg-flyout">
                  Settings
                </div>
              )}
            </Link>

            {/* Collapse Toggle Button */}
            <button
              onClick={() => setIsNavCollapsed(!isNavCollapsed)}
              className="flex items-center justify-center p-2 rounded-pg-sm text-pg-ink-subtle hover:bg-pg-surface-hover hover:text-pg-ink transition-colors cursor-pointer btn-tactile"
              aria-label={isNavCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {isNavCollapsed ? <ChevronRight20Regular /> : (
                <div className="flex items-center gap-3 w-full px-1">
                  <ChevronLeft20Regular className="w-5 h-5 flex-shrink-0" />
                  <span className="text-xs tracking-wide">Collapse</span>
                </div>
              )}
            </button>
          </div>
        </nav>

        {/* Content Canvas */}
        <main className="flex-1 overflow-y-auto min-w-0 bg-pg-app-background flex flex-col">
          {children}
        </main>
      </div>
    </div>
  );
}

function SidebarNavItems({
  isNavCollapsed,
  pathname,
  getBadgeValue
}: {
  isNavCollapsed: boolean;
  pathname: string;
  getBadgeValue: (key?: NavItem['badgeKey']) => number;
}) {
  const searchParams = useSearchParams();

  const navItems: NavItem[] = [
    { name: 'Dashboard', href: '/', icon: Board20Regular },
    { name: 'Verification Runs', href: '/runs', icon: TableSimple20Regular },
    { name: 'SOP Library', href: '/sop-library', icon: DocumentBulletList20Regular },
    { name: 'Video Evidence', href: '/video-evidence', icon: Video20Regular },
    { name: 'Deviations', href: '/runs?tab=STEPS&filter=Deviation%20Detected', icon: Alert20Regular, badgeKey: 'deviation' },
    { name: 'Human Review', href: '/runs?tab=REVIEW', icon: PersonFeedback20Regular, badgeKey: 'review_queue_count' },
    { name: 'Audit Trail', href: '/runs?tab=AUDIT', icon: History20Regular },
    { name: 'Report Export', href: '/export', icon: DocumentArrowDown20Regular }
  ];

  return (
    <div className="flex flex-col gap-0.5 p-2">
      {navItems.map(item => {
        let isActive = false;
        
        if (item.href === '/') {
          isActive = pathname === '/';
        } else if (item.href.startsWith('/runs?')) {
          if (pathname === '/runs') {
            const urlObj = new URL(item.href, 'http://localhost');
            const targetTab = urlObj.searchParams.get('tab');
            const targetFilter = urlObj.searchParams.get('filter');
            const currentTab = searchParams.get('tab') || 'OVERVIEW';
            const currentFilter = searchParams.get('filter') || 'ALL';

            if (targetTab === currentTab) {
              if (!targetFilter || targetFilter === currentFilter) {
                isActive = true;
              }
            }
          }
        } else {
          isActive = pathname === item.href || (item.href !== '/runs' && pathname.startsWith(item.href));
        }

        const badgeVal = getBadgeValue(item.badgeKey);
        
        return (
          <Link
            key={item.name}
            href={item.href}
            className={`flex items-center justify-between px-2.5 py-2 rounded-pg-sm group transition-all relative btn-tactile ${
              isActive 
                ? 'bg-pg-primary-subtle text-pg-primary font-semibold border-l-2 border-pg-primary' 
                : 'text-pg-ink-muted hover:bg-pg-surface-hover hover:text-pg-ink'
            }`}
          >
            <div className="flex items-center gap-3">
              <item.icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-pg-primary' : 'text-pg-ink-muted group-hover:text-pg-ink'}`} />
              {!isNavCollapsed && <span className="text-xs tracking-wide">{item.name}</span>}
            </div>

            {/* Badge Counter */}
            {!isNavCollapsed && badgeVal > 0 && (
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                item.badgeKey === 'deviation'
                  ? 'bg-pg-semantic-error-bg text-pg-semantic-error'
                  : 'bg-pg-semantic-review-bg text-pg-semantic-review'
              }`}>
                {badgeVal}
              </span>
            )}

            {/* Tooltip for Collapsed nav */}
            {isNavCollapsed && (
              <div className="absolute left-14 bg-pg-inverse-canvas text-pg-inverse-ink text-[11px] px-2.5 py-1 rounded-pg-sm opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50 font-sans shadow-pg-flyout">
                {item.name} {badgeVal > 0 ? `(${badgeVal})` : ''}
              </div>
            )}
          </Link>
        );
      })}
    </div>
  );
}
