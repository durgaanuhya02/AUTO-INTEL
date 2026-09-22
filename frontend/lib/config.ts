/** Agent backend (backend/main.py). Analytics-only components still use the production server on :8001. */
export const AGENT_API_URL: string =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/** ws(s)://host:port/ws derived from the REST base URL unless NEXT_PUBLIC_WS_URL is set. */
export function deriveWsUrl(apiUrl: string): string {
  const url = new URL(apiUrl);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  url.pathname = '/ws';
  url.search = '';
  url.hash = '';
  return url.toString();
}

export const AGENT_WS_URL: string =
  process.env.NEXT_PUBLIC_WS_URL || deriveWsUrl(AGENT_API_URL);
