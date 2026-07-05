import { useEffect, useState } from "react";
import { clearApiLog, subscribeApiLog, type ApiLogEntry } from "../api/apiLog";

function statusColor(status: number | null): string {
  if (status === null) return "text-gray-400";
  if (status < 300) return "text-green-600 dark:text-green-400";
  if (status < 400) return "text-blue-600 dark:text-blue-400";
  return "text-red-600 dark:text-red-400";
}

export function ApiLogPanel() {
  // Replié par défaut : ouvert, le panneau se superpose au contenu de la page
  // (boutons d'action des tableaux compris) et intercepterait les clics.
  const [open, setOpen] = useState(false);
  const [entries, setEntries] = useState<ApiLogEntry[]>([]);

  useEffect(() => subscribeApiLog(setEntries), []);

  return (
    <div
      className={`fixed bottom-4 right-4 z-50 border border-gray-300 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-900 sm:rounded-lg ${
        open ? "w-full max-w-xl" : "w-auto"
      }`}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200"
      >
        <span>API log ({entries.length})</span>
        <span className="flex items-center gap-3">
          {open && (
            <span
              onClick={(e) => {
                e.stopPropagation();
                clearApiLog();
              }}
              className="text-xs font-normal text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              effacer
            </span>
          )}
          {open ? "▾" : "▴"}
        </span>
      </button>
      {open && (
        <div className="max-h-72 overflow-y-auto border-t border-gray-200 dark:border-gray-700">
          {entries.length === 0 && (
            <p className="p-4 text-sm text-gray-400">Aucun appel API pour l'instant.</p>
          )}
          <ul className="divide-y divide-gray-100 text-xs dark:divide-gray-800">
            {entries.map((e) => (
              <li key={e.id} className="px-4 py-2">
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-gray-400">{e.timestamp}</span>
                  <span className="font-semibold text-gray-700 dark:text-gray-200">{e.method}</span>
                  <span className="truncate text-gray-600 dark:text-gray-400">{e.path}</span>
                  <span className={`ml-auto font-semibold ${statusColor(e.status)}`}>
                    {e.status ?? "erreur"}
                  </span>
                </div>
                {e.error && (
                  <pre className="mt-1 overflow-x-auto whitespace-pre-wrap break-all text-red-600 dark:text-red-400">
                    {e.error}
                  </pre>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
