// Petit magasin d'état pour le panneau "API log" : enregistre chaque appel
// (méthode, chemin, statut, éventuel corps d'erreur) sans dépendance externe.

export interface ApiLogEntry {
  id: number;
  method: string;
  path: string;
  status: number | null;
  error: string | null;
  timestamp: string;
}

type Listener = (entries: ApiLogEntry[]) => void;

let entries: ApiLogEntry[] = [];
let nextId = 1;
const listeners = new Set<Listener>();

function notify() {
  for (const listener of listeners) listener(entries);
}

export function logApiCall(entry: Omit<ApiLogEntry, "id" | "timestamp">) {
  entries = [
    { ...entry, id: nextId++, timestamp: new Date().toLocaleTimeString() },
    ...entries,
  ].slice(0, 100);
  notify();
}

export function clearApiLog() {
  entries = [];
  notify();
}

export function subscribeApiLog(listener: Listener): () => void {
  listeners.add(listener);
  listener(entries);
  return () => listeners.delete(listener);
}
