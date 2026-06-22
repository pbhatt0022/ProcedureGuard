import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  ctx: { params: Promise<{ runId: string; stepId: string }> }
) {
  try {
    const { runId, stepId } = await ctx.params;

    // Prevent path traversal
    if (!/^run-[\w-]+$/.test(runId) || !/^[\w-]+$/.test(stepId)) {
      return NextResponse.json({ error: 'Invalid run ID or step ID' }, { status: 400 });
    }

    const runsDir = process.env.PROCEDUREGUARD_RUNS_DIR || path.join(process.cwd(), '..', 'runs');
    const keyframePath = path.join(runsDir, runId, 'keyframes', `${stepId}.jpg`);

    if (fs.existsSync(keyframePath)) {
      const fileBuffer = fs.readFileSync(keyframePath);
      return new Response(fileBuffer, {
        headers: {
          'Content-Type': 'image/jpeg',
          'Cache-Control': 'public, max-age=31536000, immutable',
        },
      });
    }

    // Fallback: Return a clean, professional SVG placeholder
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 225" width="100%" height="100%">
        <rect width="100%" height="100%" fill="#111213"/>
        <rect x="10" y="10" width="380" height="205" rx="6" fill="#1b1c1e" stroke="#2c2d30" stroke-width="1.5"/>
        <path d="M 10,10 L 390,215 M 10,215 L 390,10" stroke="#222326" stroke-width="1"/>
        <circle cx="200" cy="95" r="28" fill="#141517" stroke="#3c3d42" stroke-width="1.5"/>
        <path d="M 190,85 L 210,95 L 190,105 Z" fill="#4f46e5"/>
        <text x="50%" y="150" text-anchor="middle" fill="#a1a1aa" font-family="monospace" font-size="11" font-weight="bold" letter-spacing="1">EVIDENCE KEYFRAME</text>
        <text x="50%" y="170" text-anchor="middle" fill="#71717a" font-family="monospace" font-size="10">${runId} / ${stepId}</text>
        <text x="50%" y="190" text-anchor="middle" fill="#3b82f6" font-family="monospace" font-size="8" font-weight="bold">[STANDALONE DEMO FALLBACK]</text>
      </svg>
    `.trim();

    return new Response(svg, {
      headers: {
        'Content-Type': 'image/svg+xml',
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    console.error('Failed to serve keyframe:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
