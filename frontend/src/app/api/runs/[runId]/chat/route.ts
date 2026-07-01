import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export const dynamic = 'force-dynamic';

const PROJECT_ROOT = path.resolve(process.cwd(), '..');
const BRIDGE = path.join(PROJECT_ROOT, 'scripts', 'qa_answer.py');

function callQAAgent(question: string, runId: string, sessionId: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({ question, run_id: runId, session_id: sessionId });
    const proc = spawn('python', [BRIDGE, payload], { cwd: PROJECT_ROOT, timeout: 60_000 });

    const out: Buffer[] = [];
    const err: Buffer[] = [];
    proc.stdout.on('data', (d: Buffer) => out.push(d));
    proc.stderr.on('data', (d: Buffer) => err.push(d));

    proc.on('close', (code: number | null) => {
      if (code !== 0) {
        reject(new Error(`QA agent exited ${code}: ${Buffer.concat(err).toString().trim()}`));
        return;
      }
      try {
        const parsed = JSON.parse(Buffer.concat(out).toString().trim());
        if (parsed.error) { reject(new Error(parsed.error)); return; }
        resolve(parsed.answer as string);
      } catch {
        reject(new Error('Could not parse QA agent response'));
      }
    });

    proc.on('error', (e: Error) => reject(e));
  });
}

export async function POST(
  request: NextRequest,
  ctx: { params: Promise<{ runId: string }> }
) {
  const { runId } = await ctx.params;

  if (!/^run-[\w-]+$/.test(runId)) {
    return NextResponse.json({ error: 'Invalid run ID' }, { status: 400 });
  }

  const body = await request.json();
  const question: string = (body.question ?? '').trim();
  const sessionId: string = body.sessionId ?? 'default';

  if (!question) {
    return NextResponse.json({ error: 'Question is required' }, { status: 400 });
  }

  try {
    const answer = await callQAAgent(question, runId, sessionId);
    return NextResponse.json({ answer });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'QA agent failed';
    console.error('[chat] QA agent error:', msg);
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
