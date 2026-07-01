export const ESCALATION_PATH: Record<string, string | null> = {
  'QA Log': 'Supervisor',
  'Supervisor': 'QA Manager',
  'QA Manager': 'Production Manager',
  'Production Manager': null,
};

export const SLA_POLICY: Record<string, { remind: number; escalate: number }> = {
  critical: { remind: 30,   escalate: 60   },
  high:     { remind: 120,  escalate: 240  },
  medium:   { remind: 720,  escalate: 1440 },
  low:      { remind: 2160, escalate: 4320 },
};
