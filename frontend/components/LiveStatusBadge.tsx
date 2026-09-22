'use client';

import type { ConnectionStatus } from '../lib/realtime';

interface Props {
  status: ConnectionStatus;
  /** Set when the last REST refresh failed; the panel keeps showing the last good data. */
  error?: string | null;
}

/** Shows whether the panel is receiving live updates, and never hides a failed refresh. */
export default function LiveStatusBadge({ status, error }: Props) {
  const live = status === 'open';
  return (
    <div className="flex items-center justify-end space-x-3 text-xs" data-testid="live-status">
      {error && (
        <span className="text-red-400" role="alert">
          Couldn&apos;t refresh from the agent backend ({error}) — showing last known data
        </span>
      )}
      <span className={live ? 'text-green-400' : 'text-yellow-400'}>
        <span
          className={`inline-block w-2 h-2 rounded-full mr-1 ${live ? 'bg-green-400' : 'bg-yellow-400'}`}
          aria-hidden="true"
        />
        {live ? 'Live' : status === 'connecting' ? 'Connecting…' : 'Reconnecting…'}
      </span>
    </div>
  );
}
