import { AGENT_WS_URL } from './config';

export type ConnectionStatus = 'connecting' | 'open' | 'closed';
export type FrameHandler = (data: any, frame: any) => void;

export interface RealtimeOptions {
  url: string;
  /** How often to ping while connected. */
  heartbeatMs?: number;
  /** Close and reconnect if nothing (not even a pong) has arrived for this long. */
  staleAfterMs?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  WebSocketImpl?: typeof WebSocket;
  random?: () => number;
}

/**
 * One shared, self-healing WebSocket connection.
 *
 * - Reference counted: connects on the first `retain()`, closes on the last `release()`.
 * - Reconnects forever with capped exponential backoff + jitter (a 24/7 dashboard must not
 *   give up after N attempts), and never reconnects after an intentional close.
 * - Heartbeats detect half-open connections that never fire `onclose`.
 */
export class RealtimeClient {
  status: ConnectionStatus = 'closed';

  private readonly opts: Required<Omit<RealtimeOptions, 'WebSocketImpl'>> & { WebSocketImpl?: typeof WebSocket };
  private ws: WebSocket | null = null;
  private refCount = 0;
  private attempt = 0;
  private lastSeen = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private handlers = new Map<string, Set<FrameHandler>>();
  private statusListeners = new Set<(status: ConnectionStatus) => void>();

  constructor(options: RealtimeOptions) {
    this.opts = {
      heartbeatMs: 25_000,
      staleAfterMs: 70_000,
      baseDelayMs: 1_000,
      maxDelayMs: 30_000,
      random: Math.random,
      ...options,
    };
  }

  retain(): void {
    this.refCount += 1;
    if (this.refCount === 1) this.connect();
  }

  release(): void {
    this.refCount = Math.max(0, this.refCount - 1);
    if (this.refCount === 0) this.close();
  }

  /** Subscribe to frames of `type` ('*' for all). Returns an unsubscribe function. */
  on(type: string, handler: FrameHandler): () => void {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set());
    this.handlers.get(type)!.add(handler);
    return () => this.handlers.get(type)?.delete(handler);
  }

  onStatus(listener: (status: ConnectionStatus) => void): () => void {
    this.statusListeners.add(listener);
    return () => this.statusListeners.delete(listener);
  }

  send(message: unknown): boolean {
    if (this.ws && this.ws.readyState === 1 /* OPEN */) {
      this.ws.send(JSON.stringify(message));
      return true;
    }
    return false;
  }

  private setStatus(status: ConnectionStatus) {
    if (this.status === status) return;
    this.status = status;
    this.statusListeners.forEach((listener) => {
      try {
        listener(status);
      } catch (error) {
        console.error('Realtime status listener failed:', error);
      }
    });
  }

  private connect() {
    this.clearReconnect();
    const Impl = this.opts.WebSocketImpl ?? WebSocket;
    this.setStatus('connecting');

    let ws: WebSocket;
    try {
      ws = new Impl(this.opts.url);
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      this.scheduleReconnect();
      return;
    }
    this.ws = ws;

    ws.onopen = () => {
      if (this.ws !== ws) return;
      this.attempt = 0;
      this.lastSeen = Date.now();
      this.setStatus('open');
      this.startHeartbeat();
    };

    ws.onmessage = (event: MessageEvent) => {
      if (this.ws !== ws) return;
      this.lastSeen = Date.now();
      let frame: any;
      try {
        frame = JSON.parse(event.data);
      } catch {
        console.warn('Ignoring non-JSON WebSocket frame');
        return;
      }
      if (!frame || typeof frame !== 'object' || typeof frame.type !== 'string') return;
      this.dispatch(frame);
    };

    ws.onclose = () => {
      if (this.ws !== ws) return; // a stale socket that we already replaced
      this.ws = null;
      this.stopHeartbeat();
      this.setStatus('closed');
      if (this.refCount > 0) this.scheduleReconnect();
    };

    ws.onerror = () => {
      // A close event always follows; reconnection is handled there.
    };
  }

  private dispatch(frame: { type: string; data?: unknown }) {
    const targets = [
      ...Array.from(this.handlers.get(frame.type) ?? []),
      ...Array.from(this.handlers.get('*') ?? []),
    ];
    for (const handler of targets) {
      try {
        handler(frame.data, frame);
      } catch (error) {
        console.error(`Realtime handler for '${frame.type}' failed:`, error);
      }
    }
  }

  private scheduleReconnect() {
    if (this.reconnectTimer || this.refCount === 0) return;
    const ceiling = Math.min(this.opts.maxDelayMs, this.opts.baseDelayMs * 2 ** this.attempt);
    const delay = Math.round(ceiling * (0.5 + this.opts.random() / 2)); // jitter avoids thundering herds
    this.attempt += 1;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (this.refCount > 0) this.connect();
    }, delay);
  }

  private clearReconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
  }

  private startHeartbeat() {
    this.stopHeartbeat();
    this.heartbeatTimer = setInterval(() => {
      if (Date.now() - this.lastSeen > this.opts.staleAfterMs) {
        this.ws?.close(); // half-open connection: force the reconnect path
        return;
      }
      this.send({ type: 'ping' });
    }, this.opts.heartbeatMs);
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) clearInterval(this.heartbeatTimer);
    this.heartbeatTimer = null;
  }

  private close() {
    this.clearReconnect();
    this.stopHeartbeat();
    const ws = this.ws;
    this.ws = null; // detach first so onclose doesn't schedule a reconnect
    this.attempt = 0;
    if (ws) ws.close(1000, 'client done');
    this.setStatus('closed');
  }
}

let shared: RealtimeClient | null = null;

/** Lazily created so importing this module during SSR never touches `WebSocket`. */
export function getRealtime(): RealtimeClient {
  if (!shared) shared = new RealtimeClient({ url: AGENT_WS_URL });
  return shared;
}
