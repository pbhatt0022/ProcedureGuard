import { NextResponse } from 'next/server';
import { listRuns } from '../../../lib/runStore';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const runs = await listRuns();
    return NextResponse.json(runs);
  } catch (error) {
    console.error('Failed to list runs:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
