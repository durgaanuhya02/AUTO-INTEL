import { useEffect, useRef, useState } from 'react';
import { ConnectionStatus, getRealtime } from '../lib/realtime';

type Handlers = Record<string, (data: any) => void>;

/**
 * Subscribe a component to live agent frames (`new_alert`, `new_decision`, `agent_update`, ...).
 *
 * All components share one WebSocket. Handlers may change identity every render; the latest
 * ones are always used without resubscribing (so re-renders never cause reconnects).
 */
export function useRealtime(handlers: Handlers): { status: ConnectionStatus; isConnected: boolean } {
  const [status, setStatus] = useState<ConnectionStatus>('closed');
  const latest = useRef(handlers);
  latest.current = handlers;

  // The set of subscribed frame types is fixed for the lifetime of the component.
  const typesRef = useRef(Object.keys(handlers));

  useEffect(() => {
    const client = getRealtime();
    const unsubscribers = typesRef.current.map((type) =>
      client.on(type, (data) => latest.current[type]?.(data))
    );
    unsubscribers.push(client.onStatus(setStatus));
    setStatus(client.status);
    client.retain();

    return () => {
      unsubscribers.forEach((unsubscribe) => unsubscribe());
      client.release();
    };
  }, []);

  return { status, isConnected: status === 'open' };
}
