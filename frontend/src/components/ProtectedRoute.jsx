import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/**
 * Protects customer-only routes.
 * If user is not authenticated, redirects to /login.
 * If user is an ADMIN, redirects to /admin to prevent accidental customer actions.
 */
export default function ProtectedRoute({ children, allowAdmin = false }) {
  const { user, isAdmin } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (isAdmin && !allowAdmin) {
    return <Navigate to="/admin" replace />;
  }
  return children;
}
