import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { loadTicketsDb, saveTicketsDb, findTicketKey, utcStamp } from '../../../../lib/ticketStore';
import { ESCALATION_PATH } from '../../../../lib/slaPolicy';

export const dynamic = 'force-dynamic';

export async function GET(
  _req: NextRequest,
  ctx: { params: Promise<{ ticketId: string }> }
) {
  const { ticketId } = await ctx.params;
  const db = loadTicketsDb();
  const key = findTicketKey(db, ticketId);
  if (!key) return NextResponse.json({ error: 'Not found' }, { status: 404 });
  return NextResponse.json({ key, ticket: db[key] });
}

export async function PATCH(
  req: NextRequest,
  ctx: { params: Promise<{ ticketId: string }> }
) {
  const { ticketId } = await ctx.params;
  const { action, comment, by } = await req.json();

  const db = loadTicketsDb();
  const key = findTicketKey(db, ticketId);
  if (!key) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  const ticket = db[key];
  const n = utcStamp();

  const flushComment = () => {
    if (comment?.trim()) {
      ticket.comments.push({ author: by, at: n, text: comment.trim() });
      ticket.history.push({ action: 'Comment added', by, at: n });
    }
  };

  switch (action) {
    case 'comment':
      if (!comment?.trim()) return NextResponse.json({ error: 'Empty comment' }, { status: 400 });
      ticket.comments.push({ author: by, at: n, text: comment.trim() });
      ticket.history.push({ action: 'Comment added', by, at: n });
      if (ticket.status === 'Open') {
        ticket.status = 'In Review';
        ticket.history.push({ action: 'Status → In Review', by, at: n });
      }
      break;

    case 'close':
      flushComment();
      ticket.status = 'Closed';
      ticket.history.push({ action: 'Ticket closed', by, at: n });
      break;

    case 'escalate': {
      const next = ESCALATION_PATH[ticket.assigned_to];
      if (!next) return NextResponse.json({ error: 'Already at top escalation level' }, { status: 400 });
      flushComment();
      ticket.history.push({ action: `Escalated: ${ticket.assigned_to} → ${next}`, by, at: n });
      ticket.assigned_to = next;
      ticket.status = 'Escalated';
      break;
    }

    case 'mark_compliant':
      ticket.status = 'Closed';
      ticket.history.push({ action: 'Reviewed — marked Compliant (step confirmed acceptable)', by, at: n });
      break;

    case 'promote_incident':
      ticket.verdict = 'Deviation';
      ticket.status = 'Open';
      ticket.history.push({ action: 'Reviewed — promoted to Deviation incident', by, at: n });
      break;

    default:
      return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
  }

  db[key] = ticket;
  saveTicketsDb(db);
  return NextResponse.json({ key, ticket });
}
