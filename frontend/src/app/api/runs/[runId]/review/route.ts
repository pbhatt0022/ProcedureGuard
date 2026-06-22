import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getRun, updateRun } from '../../../../../lib/runStore';

export const dynamic = 'force-dynamic';

export async function POST(
  request: NextRequest,
  ctx: { params: Promise<{ runId: string }> }
) {
  try {
    const { runId } = await ctx.params;

    // Prevent path traversal
    if (!/^run-[\w-]+$/.test(runId)) {
      return NextResponse.json({ error: 'Invalid run ID' }, { status: 400 });
    }

    const { itemId, override } = await request.json();
    if (!itemId) {
      return NextResponse.json({ error: 'itemId is required' }, { status: 400 });
    }

    const run = await getRun(runId);
    if (!run) {
      return NextResponse.json({ error: 'Run not found' }, { status: 404 });
    }

    // Get current overrides
    const currentOverrides = (run as any).reviewer_overrides || {};
    
    // Merge new override details
    const existing = currentOverrides[itemId] || {};
    const updatedOverride = {
      ...existing,
      ...override,
      timestamp: override.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      reviewer: override.reviewer || 'QA Manager',
    };

    // If verdict is reset (removed override), we can clean it up or just store it.
    // Let's store it as is, or remove the entry if the status is null.
    const newOverrides = {
      ...currentOverrides,
      [itemId]: updatedOverride,
    };

    const success = await updateRun(runId, {
      reviewer_overrides: newOverrides
    } as any);

    if (!success) {
      return NextResponse.json({ error: 'Failed to save reviewer override' }, { status: 500 });
    }

    return NextResponse.json({ success: true, overrides: newOverrides });
  } catch (error: any) {
    console.error('Failed to save reviewer override:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
