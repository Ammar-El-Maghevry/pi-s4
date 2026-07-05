import { useEffect, useState } from "react";
import { fetchMe } from "../api/auth";
import { extractErrorMessage } from "../api/client";
import type { UserRead } from "../types/api";
import { Card, ErrorBanner } from "../components/ui";

export function DashboardPage() {
  const [me, setMe] = useState<UserRead | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMe()
      .then(setMe)
      .catch((err) => setError(extractErrorMessage(err)));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Dashboard</h1>
      <Card className="max-w-md">
        <p className="mb-2 text-sm text-gray-500 dark:text-gray-400">
          Confirme que le jeton est valide via <code className="text-xs">GET /api/v1/auth/me</code>.
        </p>
        <ErrorBanner message={error} />
        {me && (
          <dl className="space-y-1 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500 dark:text-gray-400">Email</dt>
              <dd className="text-gray-900 dark:text-gray-100">{me.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500 dark:text-gray-400">Nom</dt>
              <dd className="text-gray-900 dark:text-gray-100">{me.full_name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500 dark:text-gray-400">Actif</dt>
              <dd className="text-gray-900 dark:text-gray-100">{me.is_active ? "oui" : "non"}</dd>
            </div>
          </dl>
        )}
      </Card>
    </div>
  );
}
