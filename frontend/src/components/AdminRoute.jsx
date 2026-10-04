import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/** Redirects non-admins away from admin-only pages. */
export default function AdminRoute({ children }) {
  const { user, isAdmin } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (!isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}
