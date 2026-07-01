import { NextResponse } from 'next/server';
import { loadTicketsDb } from '../../../lib/ticketStore';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    return NextResponse.json(loadTicketsDb());
  } catch (e) {
    console.error('Failed to load tickets:', e);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
