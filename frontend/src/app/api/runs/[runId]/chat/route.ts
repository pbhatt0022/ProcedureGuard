import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getRun } from '../../../../../lib/runStore';
import { AzureOpenAI } from 'openai';
import { DefaultAzureCredential, getBearerTokenProvider } from '@azure/identity';

const endpoint = process.env.AZURE_OPENAI_ENDPOINT || '';
const deployment = process.env.AZURE_OPENAI_DEPLOYMENT_NAME || 'gpt-4o';
const apiVersion = process.env.AZURE_OPENAI_API_VERSION || '2025-01-01-preview';
const apiKey = process.env.AZURE_OPENAI_API_KEY || '';

export const dynamic = 'force-dynamic';

const SYSTEM_PROMPT = `You are a manufacturing compliance assistant for ProcedureGuard.
Answer questions about a specific verification run using only the data provided.
Be concise and specific. Reference step IDs and timestamps when relevant.
If a step is Unable to Verify, explain that the system abstained rather than guessing.
Never fabricate information not present in the verdicts data.`;

function buildContext(runId: string, results: any): string {
  const summary = results.summary || {};
  const score = results.adherence_score;
  const scoreStr = (score !== null && score !== undefined) ? `${Math.round(score * 100)}%` : 'N/A';

  const lines = [
    `Run ID: ${runId}`,
    `Adherence score: ${scoreStr}  |  ` +
    `${summary.compliant || 0} Compliant / ` +
    `${summary.deviation || 0} Deviation Detected / ` +
    `${summary.requires_inspection || 0} Requires Inspection / ` +
    `${summary.unable_to_verify || 0} Unable to Verify`,
    '',
    'Verdicts:',
  ];

  const verdicts = results.verdicts || [];
  for (const v of verdicts) {
    const confidencePct = Math.round((v.confidence || 0) * 100);
    const tsStart = v.evidence_timestamp_start;
    const tsEnd = v.evidence_timestamp_end;
    const ts = (tsStart !== null && tsStart !== undefined) ? `${tsStart}s – ${tsEnd}s` : 'no timestamp';
    lines.push(`[${v.step_id}] ${v.criterion || ''} — ${v.verdict} (${confidencePct}%)`);
    lines.push(`  Timestamps: ${ts}`);
    if (v.reasoning) {
      lines.push(`  Reasoning: ${v.reasoning}`);
    }
  }

  return lines.join('\n');
}

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

    const { question } = await request.json();
    if (!question) {
      return NextResponse.json({ error: 'Question is required' }, { status: 400 });
    }

    const run = await getRun(runId);
    if (!run) {
      return NextResponse.json({ error: 'Run not found' }, { status: 404 });
    }

    const contextText = buildContext(runId, run);

    // Initialize Azure OpenAI client
    let client: AzureOpenAI;
    if (apiKey) {
      client = new AzureOpenAI({
        endpoint,
        apiVersion,
        apiKey
      });
    } else {
      const credential = new DefaultAzureCredential();
      const scope = 'https://cognitiveservices.azure.com/.default';
      const azureADTokenProvider = getBearerTokenProvider(credential, scope);
      client = new AzureOpenAI({
        endpoint,
        apiVersion,
        azureADTokenProvider
      });
    }

    const response = await client.chat.completions.create({
      model: deployment,
      messages: [
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: `${contextText}\n\nQuestion: ${question}` }
      ],
      max_tokens: 500,
      temperature: 0
    });

    const answer = response.choices[0]?.message?.content?.trim() || 'No answer generated.';
    return NextResponse.json({ answer });
  } catch (error: any) {
    console.error('Failed to answer chat question:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
