import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { RealtimeClient } from '../realtime';

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  readyState = 0;
  sent: string[] = [];
  closeCode?: number;
  onopen: ((e: any) => void) | null = null;
  onmessage: ((e: any) => void) | null = null;
  onclose: ((e: any) => void) | null = null;
  onerror: ((e: any) => void) | null = null;

  constructor(public url: string) {
    FakeWebSocket.instances.push(this);
  }
  send(data: string) {
    this.sent.push(data);
  }
  close(code?: number) {
    this.closeCode = code;
    this.readyState = 3;
    this.onclose?.({ code });
  }
  // --- test helpers
  open() {
    this.readyState = 1;
    this.onopen?.({});
  }
  receive(frame: unknown) {
    this.onmessage?.({ data: typeof frame === 'string' ? frame : JSON.stringify(frame) });
  }
  drop() {
    this.readyState = 3;
    this.onclose?.({ code: 1006 });
  }
}

const sockets = () => FakeWebSocket.instances;
const latest = () => sockets()[sockets().length - 1];

function makeClient(overrides = {}) {
  return new RealtimeClient({
    url: 'ws://test/ws',
    WebSocketImpl: FakeWebSocket as unknown as typeof WebSocket,
    random: () => 1, // no jitter: delay == ceiling
    baseDelayMs: 1000,
    maxDelayMs: 8000,
    heartbeatMs: 10_000,
    staleAfterMs: 30_000,
    ...overrides,
  });
}

beforeEach(() => {
  FakeWebSocket.instances = [];
  vi.useFakeTimers();
});
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe('connection lifecycle', () => {
  it('connects on first retain and shares one socket across subscribers', () => {
    const client = makeClient();
    client.retain();
    client.retain();
    expect(sockets()).toHaveLength(1);
    expect(latest().url).toBe('ws://test/ws');
    client.release();
    expect(latest().closeCode).toBeUndefined(); // still one subscriber left
    client.release();
    expect(latest().closeCode).toBe(1000);
  });

  it('reports connecting -> open -> closed', () => {
    const client = makeClient();
    const seen: string[] = [];
    client.onStatus((s) => seen.push(s));
    client.retain();
    latest().open();
    latest().drop();
    expect(seen).toEqual(['connecting', 'open', 'closed']);
  });

  it('does not reconnect after an intentional close, even if a retry was pending', () => {
    const client = makeClient();
    client.retain();
    latest().open();
    latest().drop(); // schedules a retry
    client.release(); // component unmounted before the retry fired
    vi.advanceTimersByTime(60_000);
    expect(sockets()).toHaveLength(1);
  });

  it('ignores events from a socket that has already been replaced', () => {
    const client = makeClient();
    client.retain();
    const first = latest();
    first.open();
    first.drop();
    vi.advanceTimersByTime(1000);
    const second = latest();
    expect(second).not.toBe(first);
    second.open();
    first.drop(); // late event from the dead socket
    vi.advanceTimersByTime(5_000); // well inside the heartbeat window
    expect(sockets()).toHaveLength(2);
    expect(client.status).toBe('open');
  });
});

describe('reconnection', () => {
  it('backs off exponentially up to the cap, and never gives up', () => {
    const client = makeClient();
    client.retain();

    const delays: number[] = [];
    for (let i = 0; i < 10; i++) {
      const before = sockets().length;
      latest().drop();
      let waited = 0;
      while (sockets().length === before) {
        vi.advanceTimersByTime(250);
        waited += 250;
        expect(waited).toBeLessThanOrEqual(8000);
      }
      delays.push(waited);
    }
    expect(delays).toEqual([1000, 2000, 4000, 8000, 8000, 8000, 8000, 8000, 8000, 8000]);
    expect(sockets()).toHaveLength(11);
  });

  it('resets the backoff after a successful connection', () => {
    const client = makeClient();
    client.retain();
    latest().drop();
    vi.advanceTimersByTime(1000);
    latest().drop();
    vi.advanceTimersByTime(2000);
    latest().open(); // healthy again
    latest().drop();

    const before = sockets().length;
    vi.advanceTimersByTime(999);
    expect(sockets()).toHaveLength(before);
    vi.advanceTimersByTime(1);
    expect(sockets()).toHaveLength(before + 1);
  });

  it('applies jitter within [50%, 100%] of the ceiling', () => {
    const client = makeClient({ random: () => 0 });
    client.retain();
    latest().drop();
    vi.advanceTimersByTime(499);
    expect(sockets()).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(sockets()).toHaveLength(2);
  });

  it('survives the constructor throwing (e.g. blocked/invalid URL) and keeps retrying', () => {
    let attempts = 0;
    class Exploding extends FakeWebSocket {
      constructor(url: string) {
        super(url);
        attempts += 1;
        if (attempts < 3) throw new Error('SecurityError');
      }
    }
    const client = makeClient({ WebSocketImpl: Exploding as unknown as typeof WebSocket });
    client.retain();
    vi.advanceTimersByTime(10_000);
    expect(attempts).toBe(3);
  });
});

describe('frames', () => {
  it('routes frames to typed and wildcard handlers with the data payload', () => {
    const client = makeClient();
    const alerts = vi.fn();
    const everything = vi.fn();
    client.on('new_alert', alerts);
    client.on('*', everything);
    client.retain();
    latest().open();

    latest().receive({ type: 'new_alert', data: { title: 'x' }, timestamp: 't' });
    latest().receive({ type: 'new_decision', data: { id: 1 } });

    expect(alerts).toHaveBeenCalledTimes(1);
    expect(alerts.mock.calls[0][0]).toEqual({ title: 'x' });
    expect(everything).toHaveBeenCalledTimes(2);
  });

  it('ignores malformed frames without breaking the connection', () => {
    const client = makeClient();
    const handler = vi.fn();
    client.on('*', handler);
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    client.retain();
    latest().open();

    latest().receive('not json');
    latest().receive('[1,2]');
    latest().receive('{"data": 1}');
    latest().receive({ type: 42 });
    latest().receive({ type: 'ok' });

    expect(handler).toHaveBeenCalledTimes(1);
    expect(client.status).toBe('open');
  });

  it('a throwing handler does not stop other handlers', () => {
    const client = makeClient();
    const good = vi.fn();
    vi.spyOn(console, 'error').mockImplementation(() => {});
    client.on('new_alert', () => {
      throw new Error('boom');
    });
    client.on('new_alert', good);
    client.retain();
    latest().open();
    latest().receive({ type: 'new_alert', data: {} });
    expect(good).toHaveBeenCalled();
  });

  it('unsubscribe stops delivery', () => {
    const client = makeClient();
    const handler = vi.fn();
    const off = client.on('new_alert', handler);
    client.retain();
    latest().open();
    off();
    latest().receive({ type: 'new_alert', data: {} });
    expect(handler).not.toHaveBeenCalled();
  });

  it('send() only works while open', () => {
    const client = makeClient();
    client.retain();
    expect(client.send({ type: 'ping' })).toBe(false);
    latest().open();
    expect(client.send({ type: 'ping' })).toBe(true);
    expect(latest().sent).toEqual(['{"type":"ping"}']);
  });
});

describe('heartbeat', () => {
  it('pings periodically while open', () => {
    const client = makeClient();
    client.retain();
    latest().open();
    vi.advanceTimersByTime(10_000);
    latest().receive({ type: 'pong' });
    vi.advanceTimersByTime(10_000);
    expect(latest().sent.filter((m) => m.includes('ping'))).toHaveLength(2);
  });

  it('recycles a half-open connection that stops answering', () => {
    const client = makeClient();
    client.retain();
    const first = latest();
    first.open();

    // No pongs, no frames, and no close event: the classic dead-but-open socket.
    vi.advanceTimersByTime(40_000);
    expect(first.readyState).toBe(3);
    vi.advanceTimersByTime(1000);
    expect(sockets().length).toBeGreaterThan(1);
  });

  it('keeps a healthy connection that answers pings', () => {
    const client = makeClient();
    client.retain();
    const first = latest();
    first.open();
    for (let i = 0; i < 12; i++) {
      vi.advanceTimersByTime(10_000);
      first.receive({ type: 'pong' });
    }
    expect(sockets()).toHaveLength(1);
    expect(client.status).toBe('open');
  });

  it('stops pinging after the connection drops', () => {
    const client = makeClient({ baseDelayMs: 100_000, maxDelayMs: 100_000 });
    client.retain();
    const first = latest();
    first.open();
    first.drop();
    const sentBefore = first.sent.length;
    vi.advanceTimersByTime(60_000);
    expect(first.sent.length).toBe(sentBefore);
  });
});
