import { describe, expect, it } from 'vitest';
import {
  formatUsd,
  normalizeTimestamp,
  normalizeSeverity,
  toAgents,
  toAlert,
  toDecision,
  upsertById,
} from '../adapters';
import { deriveWsUrl } from '../config';

// Payloads below are exactly what the Python agents write to Redis / the API returns
// (see agents/observer_agent.py::_create_alert and agents/governance_agent.py::_review_decision).
const observerAlert = {
  title: 'Metric Alert: revenue',
  description: 'revenue below minimum threshold: 500.00 < 1000',
  severity: 'high',
  metric_type: 'revenue',
  current_value: 500.0,
  threshold_value: 1000,
  agent_type: 'observer',
  timestamp: '2026-01-12T12:00:00',
};

const governanceEntry = {
  decision_id: 'abc123',
  decision_title: 'Decision for revenue anomaly',
  recommended_scenario: 'Promotional Campaign',
  financial_impact: 1400.4,
  confidence_score: 0.8325,
  policy_result: {
    approved: false,
    requires_approval: true,
    violations: [
      { rule: 'critical_metrics', severity: 'medium' },
      { rule: 'restricted_scenarios', severity: 'high' },
    ],
  },
  final_status: 'pending',
  action: 'request_human_approval',
  timestamp: '2026-01-12T12:00:01',
};

describe('toAlert', () => {
  it('maps an observer alert to the panel shape', () => {
    const alert = toAlert(observerAlert)!;
    expect(alert).toMatchObject({
      type: 'high',
      title: 'Metric Alert: revenue',
      agent: 'Observer Agent',
      status: 'active',
      timestamp: '2026-01-12T12:00:00Z',
      impact: 'revenue at 500 (threshold 1000)',
    });
    expect(alert.id).toBe('revenue-2026-01-12T12:00:00Z');
  });

  it('does not fabricate a confidence the backend never sent', () => {
    expect(toAlert(observerAlert)!.confidence).toBeNull();
  });

  it('prefers a server-supplied id and resolved state', () => {
    const alert = toAlert({ ...observerAlert, id: 7, resolved_at: '2026-01-12T13:00:00' })!;
    expect(alert.id).toBe('7');
    expect(alert.status).toBe('resolved');
  });

  it.each([null, undefined, 'x', 42, [], {}, { title: 1, description: 'd' }])('rejects malformed input %j', (bad) => {
    expect(toAlert(bad)).toBeNull();
  });

  it('falls back to medium for unknown severities', () => {
    expect(toAlert({ ...observerAlert, severity: 'catastrophic' })!.type).toBe('medium');
    expect(normalizeSeverity('critical')).toBe('critical');
  });
});

describe('toDecision', () => {
  it('maps a governance audit entry', () => {
    expect(toDecision(governanceEntry)).toMatchObject({
      id: 'abc123',
      title: 'Decision for revenue anomaly',
      action: 'Promotional Campaign',
      description: 'Recommended: Promotional Campaign',
      confidence: 83.3,
      status: 'pending',
      agent: 'Governance Agent',
      category: 'marketing',
      estimatedValue: 1400.4,
      riskLevel: 'high',
      impact: 'Estimated net impact $1,400',
      reasoning: 'Governance flags: critical_metrics, restricted_scenarios',
    });
  });

  it.each([
    ['approved', 'approved'],
    ['rejected', 'rejected'],
    ['executed', 'implemented'],
    ['pending', 'pending'],
    ['???', 'pending'],
  ])('maps final_status %s -> %s', (finalStatus, expected) => {
    expect(toDecision({ ...governanceEntry, final_status: finalStatus })!.status).toBe(expected);
  });

  it('reports low risk and a clean reasoning line when there are no violations', () => {
    const decision = toDecision({ ...governanceEntry, policy_result: { violations: [] } })!;
    expect(decision.riskLevel).toBe('low');
    expect(decision.reasoning).toBe('Meets all governance policies');
  });

  it('classifies categories from the scenario name', () => {
    const category = (s: string) => toDecision({ ...governanceEntry, recommended_scenario: s })!.category;
    expect(category('Price Optimization')).toBe('pricing');
    expect(category('Inventory Clearance')).toBe('inventory');
    expect(category('Retention Offer')).toBe('marketing');
    expect(category('Logistics Optimization')).toBe('operations');
  });

  it('tolerates missing/garbage numbers without NaN reaching the UI', () => {
    const decision = toDecision({ ...governanceEntry, confidence_score: 'x', financial_impact: undefined })!;
    expect(decision.confidence).toBe(0);
    expect(decision.estimatedValue).toBe(0);
    expect(decision.impact).toBe('Impact unknown');
  });

  it('clamps confidence into 0-100', () => {
    expect(toDecision({ ...governanceEntry, confidence_score: 7 })!.confidence).toBe(100);
    expect(toDecision({ ...governanceEntry, confidence_score: -1 })!.confidence).toBe(0);
  });

  it.each([null, 'x', [], {}])('rejects malformed input %j', (bad) => {
    expect(toDecision(bad)).toBeNull();
  });
});

describe('toAgents', () => {
  const payload = {
    orchestrator_running: true,
    agents: {
      governance: { agent_type: 'governance', status: 'active', last_activity: 't3', current_task: 'Monitoring' },
      observer: { agent_type: 'observer', status: 'processing', last_activity: 't1', current_task: 'Analyzing' },
      analyst: { status: 'error' },
      simulation: { status: 'unknown' },
    },
  };

  it('always returns the five pipeline agents in pipeline order', () => {
    expect(toAgents(payload).map((a) => a.id)).toEqual(['observer', 'analyst', 'simulation', 'decision', 'governance']);
  });

  it('marks agents that stopped reporting as offline instead of hiding them', () => {
    const byId = Object.fromEntries(toAgents(payload).map((a) => [a.id, a]));
    expect(byId.simulation.status).toBe('offline');
    expect(byId.decision.status).toBe('offline'); // absent from payload
    expect(byId.decision.currentTask).toBe('No heartbeat received');
    expect(byId.analyst.status).toBe('error');
    expect(byId.observer.status).toBe('processing');
  });

  it('does not invent performance, uptime or task counts', () => {
    for (const agent of toAgents(payload)) {
      expect(agent.performance).toBeNull();
      expect(agent.uptime).toBeNull();
      expect(agent.tasksCompleted).toBeNull();
    }
  });

  it.each([null, undefined, 'x', {}, { agents: null }, { error: 'boom' }])('handles malformed payload %j', (bad) => {
    const agents = toAgents(bad);
    expect(agents).toHaveLength(5);
    expect(agents.every((a) => a.status === 'offline')).toBe(true);
  });
});

describe('upsertById', () => {
  const item = (id: string, v = 0) => ({ id, v });

  it('puts new items first and replaces existing ones instead of duplicating', () => {
    const result = upsertById([item('a', 1), item('b', 1)], item('b', 2));
    expect(result).toEqual([item('b', 2), item('a', 1)]);
  });

  it('caps the list so a long-running page cannot grow without bound', () => {
    let list: Array<{ id: string }> = [];
    for (let i = 0; i < 500; i++) list = upsertById(list, item(String(i)), 100);
    expect(list).toHaveLength(100);
    expect(list[0].id).toBe('499');
  });
});

describe('formatUsd', () => {
  it.each([
    [1400.4, '$1,400'],
    [-3400, '-$3,400'],
    [0, '$0'],
    [1234567, '$1,234,567'],
  ])('%d -> %s', (value, expected) => expect(formatUsd(value)).toBe(expected));
});

describe('deriveWsUrl', () => {
  it.each([
    ['http://localhost:8000/api/v1', 'ws://localhost:8000/ws'],
    ['https://api.example.com/api/v1', 'wss://api.example.com/ws'],
    ['http://10.0.0.5:9000/api/v1?x=1', 'ws://10.0.0.5:9000/ws'],
  ])('%s -> %s', (api, ws) => expect(deriveWsUrl(api)).toBe(ws));
});

describe('normalizeTimestamp', () => {
  it.each([
    ['2026-09-21T17:37:33.805741', '2026-09-21T17:37:33.805741Z'],
    ['2026-09-21T17:37:33', '2026-09-21T17:37:33Z'],
    ['2026-09-21T17:37', '2026-09-21T17:37Z'],
    ['2026-09-21T17:37:33Z', '2026-09-21T17:37:33Z'],
    ['2026-09-21T17:37:33+05:30', '2026-09-21T17:37:33+05:30'],
    ['2026-09-21T17:37:33.5-04:00', '2026-09-21T17:37:33.5-04:00'],
  ])('%s -> %s', (input, expected) => expect(normalizeTimestamp(input)).toBe(expected));

  it.each([undefined, null, 42, ''])('returns empty for %j', (input) => expect(normalizeTimestamp(input)).toBe(''));

  it('parses to the correct instant regardless of the viewer timezone', () => {
    const naive = '2026-01-12T12:00:00';
    expect(new Date(normalizeTimestamp(naive)).toISOString()).toBe('2026-01-12T12:00:00.000Z');
  });

  it('is applied to agent last-activity and decision timestamps', () => {
    expect(toAgents({ agents: { observer: { status: 'active', last_activity: '2026-01-12T12:00:00' } } })[0].lastActivity)
      .toBe('2026-01-12T12:00:00Z');
    expect(toDecision(governanceEntry)!.timestamp).toBe('2026-01-12T12:00:01Z');
  });
});
