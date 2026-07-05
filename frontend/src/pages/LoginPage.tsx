import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage, extractErrorStatus } from "../api/client";
import { Button, Card, ErrorBanner, Input, Label } from "../components/ui";

export function LoginPage() {
  const [email, setEmail] = useState("admin@univ.local");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { setToken } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const token = await login(email, password);
      setToken(token.access_token);
      navigate("/dashboard");
    } catch (err) {
      const status = extractErrorStatus(err);
      setError(`${status ?? "?"} — ${extractErrorMessage(err)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-950">
      <Card className="w-full max-w-sm">
        <h1 className="mb-4 text-lg font-semibold text-gray-900 dark:text-gray-100">Connexion</h1>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <Label>Email</Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div>
            <Label>Mot de passe</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <ErrorBanner message={error} />
          <Button type="submit" disabled={loading} className="w-full justify-center">
            {loading ? "Connexion..." : "Se connecter"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
