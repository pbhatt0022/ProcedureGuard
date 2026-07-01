import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import fs from 'fs';
import path from 'path';

export const dynamic = 'force-dynamic';

// Streams a run's source clip (the local dataset video) so the Evidence Workspace
// player can load and seek it. Honors HTTP Range (206) for scrubbing without
// buffering the whole file. Mirrors the keyframes route's conventions.
export async function GET(
  request: NextRequest,
  ctx: { params: Promise<{ runId: string }> }
) {
  try {
    const { runId } = await ctx.params;
    if (!/^run-[\w-]+$/.test(runId)) {
      return NextResponse.json({ error: 'Invalid run ID' }, { status: 400 });
    }

    const runsDir = process.env.PROCEDUREGUARD_RUNS_DIR || path.join(process.cwd(), '..', 'runs');
    const runFile = path.join(runsDir, `${runId}.json`);
    if (!fs.existsSync(runFile)) {
      return NextResponse.json({ error: 'Run not found' }, { status: 404 });
    }

    const run = JSON.parse(fs.readFileSync(runFile, 'utf-8'));
    const videoUrl: string = run?.observations?.video_url || '';
    if (!videoUrl) {
      return NextResponse.json({ error: 'No video for this run' }, { status: 404 });
    }

    // Only serve local files under the repo's dataset video dir (path-traversal guard).
    const videoRoot = path.resolve(process.cwd(), '..', 'industreal_selected', 'videos');
    const resolved = path.resolve(videoUrl);
    if (!resolved.startsWith(videoRoot + path.sep) || !fs.existsSync(resolved)) {
      return NextResponse.json({ error: 'Video file unavailable' }, { status: 404 });
    }

    // The raw IndustReal clips are MPEG-4 Part 2 (not browser-playable). Prefer a
    // transcoded H.264/faststart web version (industreal_selected/videos/_web/<runId>.mp4)
    // when present; fall back to the original otherwise.
    const webVersion = path.join(videoRoot, '_web', `${runId}.mp4`);
    const filePath = fs.existsSync(webVersion) ? webVersion : resolved;

    const total = fs.statSync(filePath).size;
    const range = request.headers.get('range');

    if (range) {
      const m = /bytes=(\d+)-(\d*)/.exec(range);
      const start = m ? parseInt(m[1], 10) : 0;
      // Cap open-ended ranges to ~1MB chunks so we never buffer the whole clip.
      const end = m && m[2] ? parseInt(m[2], 10) : Math.min(start + 1024 * 1024 - 1, total - 1);
      const chunkSize = end - start + 1;
      const fd = fs.openSync(filePath, 'r');
      const buf = Buffer.alloc(chunkSize);
      fs.readSync(fd, buf, 0, chunkSize, start);
      fs.closeSync(fd);
      return new Response(buf, {
        status: 206,
        headers: {
          'Content-Type': 'video/mp4',
          'Content-Range': `bytes ${start}-${end}/${total}`,
          'Accept-Ranges': 'bytes',
          'Content-Length': String(chunkSize),
          'Cache-Control': 'no-store',
        },
      });
    }

    const buf = fs.readFileSync(filePath);
    return new Response(buf, {
      headers: {
        'Content-Type': 'video/mp4',
        'Accept-Ranges': 'bytes',
        'Content-Length': String(total),
        'Cache-Control': 'no-store',
      },
    });
  } catch (error) {
    console.error('Failed to serve video:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
