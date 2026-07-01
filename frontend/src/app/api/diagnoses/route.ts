import { NextResponse } from 'next/server';
import { listDiagnoses } from '../../../lib/ticketStore';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    return NextResponse.json(listDiagnoses());
  } catch (e) {
    console.error('Failed to load diagnoses:', e);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
