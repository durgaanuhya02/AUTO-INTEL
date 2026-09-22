/**
 * Adapters from backend payloads (backend/main.py) to the shapes the dashboard panels render.
 * Where the backend doesn't provide a value, the adapter returns null rather than inventing one.
 */

export type Severity = 'critical' | 'high' | 'medium' | 'low';

export interface DashboardAlert {
  id: string;
  type: Severity;
  title: string;
  description: string;
  timestamp: string;
  agent: string;
  confidence: number | null;
  impact: string;
  status: 'active' | 'acknowledged' | 'resolved';
}

export interface DashboardDecision {
  id: string;
  title: string;
  description: string;
  action: string;
  confidence: number;
  impact: string;
  reasoning: string;
  status: 'pending' | 'approved' | 'rejected' | 'implemented';
  timestamp: string;
  agent: string;
  category: 'pricing' | 'inventory' | 'marketing' | 'operations';
  estimatedValue: number;
  riskLevel: 'low' | 'medium' | 'high';
}

export interface DashboardAgent {
  id: string;
  name: string;
  type: string;
  status: 'active' | 'idle' | 'processing' | 'error' | 'offline';
  lastActivity: string;
  currentTask: string;
  performance: number | null;
  uptime: string | null;
  tasksCompleted: number | null;
}

const isObject = (value: unknown): value is Record<string, any> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);

/**
 * The backend emits timezone-naive UTC timestamps (Python `datetime.utcnow().isoformat()`),
 * which `new Date()` would parse as *local* time and shift by the viewer's UTC offset.
 * Mark them as UTC. Values that already carry a `Z` or offset are left untouched.
 */
export function normalizeTimestamp(value: unknown): string {
  if (typeof value !== 'string' || value === '') return '';
  const isNaiveIso = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(value);
  return isNaiveIso ? `${value}Z` : value;
}

const titleCase = (text: string) => text.charAt(0).toUpperCase() + text.slice(1);
const round = (value: number, places = 2) => Number(value.toFixed(places));

export function formatUsd(value: number): string {
  const sign = value < 0 ? '-' : '';
  return `${sign}$${Math.abs(Math.round(value)).toLocaleString('en-US')}`;
}

export function normalizeSeverity(value: unknown): Severity {
  return value === 'critical' || value === 'high' || value === 'medium' || value === 'low' ? value : 'medium';
}

export function toAlert(raw: unknown): DashboardAlert | null {
  if (!isObject(raw) || typeof raw.title !== 'string' || typeof raw.description !== 'string') return null;

  const metric = String(raw.metric_type ?? 'metric');
  const timestamp = normalizeTimestamp(raw.timestamp ?? raw.created_at) || new Date().toISOString();
  const current = typeof raw.current_value === 'number' ? round(raw.current_value) : null;
  const threshold = typeof raw.threshold_value === 'number' ? round(raw.threshold_value) : null;

  let impact = metric;
  if (current !== null) impact += ` at ${current}`;
  if (threshold !== null) impact += ` (threshold ${threshold})`;

  return {
    id: String(raw.id ?? `${metric}-${timestamp}`),
    type: normalizeSeverity(raw.severity),
    title: raw.title,
    description: raw.description,
    timestamp,
    agent: `${titleCase(String(raw.agent_type ?? 'observer'))} Agent`,
    confidence: null,
    impact,
    status: raw.resolved_at ? 'resolved' : 'active',
  };
}

const CATEGORY_KEYWORDS: Array<[DashboardDecision['category'], RegExp]> = [
  ['pricing', /pric/i],
  ['inventory', /inventor|stock/i],
  ['marketing', /market|promo|campaign|retention|loyalty/i],
];

export function toDecision(raw: unknown): DashboardDecision | null {
  if (!isObject(raw)) return null;
  const title = raw.decision_title ?? raw.title;
  if (typeof title !== 'string') return null;

  const scenario = String(raw.recommended_scenario ?? '');
  const violations: Array<{ rule?: string; severity?: string }> = Array.isArray(raw.policy_result?.violations)
    ? raw.policy_result.violations
    : [];
  const impactValue = Number(raw.financial_impact);
  const confidence = Number(raw.confidence_score);

  const finalStatus = String(raw.final_status ?? 'pending');
  const status: DashboardDecision['status'] =
    finalStatus === 'approved' || finalStatus === 'rejected'
      ? finalStatus
      : finalStatus === 'executed'
        ? 'implemented'
        : 'pending';

  return {
    id: String(raw.decision_id ?? raw.id ?? raw.timestamp ?? title),
    title,
    description: scenario ? `Recommended: ${scenario}` : 'No scenario recommended',
    action: scenario,
    confidence: Number.isFinite(confidence) ? Math.min(100, Math.max(0, round(confidence * 100, 1))) : 0,
    impact: Number.isFinite(impactValue) ? `Estimated net impact ${formatUsd(impactValue)}` : 'Impact unknown',
    reasoning: violations.length
      ? `Governance flags: ${violations.map((v) => v.rule ?? 'policy').join(', ')}`
      : 'Meets all governance policies',
    status,
    timestamp: normalizeTimestamp(raw.timestamp) || new Date().toISOString(),
    agent: 'Governance Agent',
    category: CATEGORY_KEYWORDS.find(([, pattern]) => pattern.test(scenario))?.[0] ?? 'operations',
    estimatedValue: Number.isFinite(impactValue) ? impactValue : 0,
    riskLevel: violations.some((v) => v.severity === 'high') ? 'high' : violations.length ? 'medium' : 'low',
  };
}

const PIPELINE = ['observer', 'analyst', 'simulation', 'decision', 'governance'] as const;

export function toAgents(payload: unknown): DashboardAgent[] {
  const agents = isObject(payload) && isObject(payload.agents) ? payload.agents : {};

  return PIPELINE.map((key) => {
    const entry = isObject(agents[key]) ? agents[key] : {};
    const reported = String(entry.status ?? 'unknown');
    const known = reported === 'active' || reported === 'idle' || reported === 'processing' || reported === 'error';
    // Status keys expire after 5 minutes without a heartbeat, so "unknown" means the agent has stopped reporting.
    const status: DashboardAgent['status'] = known ? (reported as DashboardAgent['status']) : reported === 'initializing' ? 'processing' : 'offline';

    return {
      id: key,
      name: `${titleCase(key)} Agent`,
      type: titleCase(key),
      status,
      lastActivity: normalizeTimestamp(entry.last_activity),
      currentTask: String(entry.current_task ?? (status === 'offline' ? 'No heartbeat received' : '')),
      performance: null,
      uptime: null,
      tasksCompleted: null,
    };
  });
}

/** Insert or replace by id, newest first, capped so a long-running page can't grow without bound. */
export function upsertById<T extends { id: string }>(items: T[], incoming: T, cap = 100): T[] {
  return [incoming, ...items.filter((item) => item.id !== incoming.id)].slice(0, cap);
}
