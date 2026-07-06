import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import type { Role } from "../lib/types";

export function ProtectedRoute({ allow, fallback = "/" }: { allow?: Role[]; fallback?: string }) {
  const { user, isLoading } = useAuth();

  if (isLoading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (allow && !allow.includes(user.role)) return <Navigate to={fallback} replace />;

  return <Outlet />;
}
