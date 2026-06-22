import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getRun } from '../../../../lib/runStore';

export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  ctx: { params: Promise<{ runId: string }> }
) {
  try {
    const { runId } = await ctx.params;
    const run = await getRun(runId);
    
    if (!run) {
      return NextResponse.json({ error: 'Run not found' }, { status: 404 });
    }
    
    return NextResponse.json(run);
  } catch (error) {
    console.error('Failed to get run:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
