import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminRoute from "./components/AdminRoute";
import Layout from "./components/Layout";

import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Accounts from "./pages/Accounts";
import AccountDetails from "./pages/AccountDetails";
import Transfer from "./pages/Transfer";
import Deposit from "./pages/Deposit";
import Withdraw from "./pages/Withdraw";
import Transactions from "./pages/Transactions";
import Beneficiaries from "./pages/Beneficiaries";
import AccountClosure from "./pages/AccountClosure";
import Profile from "./pages/Profile";

import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminCustomers from "./pages/admin/AdminCustomers";
import AdminCustomerDetail from "./pages/admin/AdminCustomerDetail";
import AdminAccounts from "./pages/admin/AdminAccounts";
import AdminTransactions from "./pages/admin/AdminTransactions";
import AdminAccountRequests from "./pages/admin/AdminAccountRequests";
import AdminClosureRequests from "./pages/admin/AdminClosureRequests";
import AdminAuditLogs from "./pages/admin/AdminAuditLogs";
import AdminAdmins from "./pages/admin/AdminAdmins";

function HomeRedirect() {
  const { user, isAdmin } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={isAdmin ? "/admin" : "/dashboard"} replace />;
}

function withLayout(element) {
  return <Layout>{element}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          <Route path="/" element={<HomeRedirect />} />

          {/* Customer routes */}
          <Route
            path="/dashboard"
            element={<ProtectedRoute>{withLayout(<Dashboard />)}</ProtectedRoute>}
          />
          <Route
            path="/accounts"
            element={<ProtectedRoute>{withLayout(<Accounts />)}</ProtectedRoute>}
          />
          <Route
            path="/accounts/:id"
            element={<ProtectedRoute>{withLayout(<AccountDetails />)}</ProtectedRoute>}
          />
          <Route
            path="/transfer"
            element={<ProtectedRoute>{withLayout(<Transfer />)}</ProtectedRoute>}
          />
          <Route
            path="/deposit"
            element={<ProtectedRoute>{withLayout(<Deposit />)}</ProtectedRoute>}
          />
          <Route
            path="/withdraw"
            element={<ProtectedRoute>{withLayout(<Withdraw />)}</ProtectedRoute>}
          />
          <Route
            path="/transactions"
            element={<ProtectedRoute>{withLayout(<Transactions />)}</ProtectedRoute>}
          />
          <Route
            path="/beneficiaries"
            element={<ProtectedRoute>{withLayout(<Beneficiaries />)}</ProtectedRoute>}
          />
          <Route
            path="/account-closure"
            element={<ProtectedRoute>{withLayout(<AccountClosure />)}</ProtectedRoute>}
          />
          <Route
            path="/profile"
            element={<ProtectedRoute>{withLayout(<Profile />)}</ProtectedRoute>}
          />

          {/* Admin routes */}
          <Route
            path="/admin"
            element={<AdminRoute>{withLayout(<AdminDashboard />)}</AdminRoute>}
          />
          <Route
            path="/admin/customers"
            element={<AdminRoute>{withLayout(<AdminCustomers />)}</AdminRoute>}
          />
          <Route
            path="/admin/customers/:id"
            element={<AdminRoute>{withLayout(<AdminCustomerDetail />)}</AdminRoute>}
          />
          <Route
            path="/admin/administrators"
            element={<AdminRoute>{withLayout(<AdminAdmins />)}</AdminRoute>}
          />
          <Route
            path="/admin/accounts"
            element={<AdminRoute>{withLayout(<AdminAccounts />)}</AdminRoute>}
          />
          <Route
            path="/admin/transactions"
            element={<AdminRoute>{withLayout(<AdminTransactions />)}</AdminRoute>}
          />
          <Route
            path="/admin/account-requests"
            element={<AdminRoute>{withLayout(<AdminAccountRequests />)}</AdminRoute>}
          />
          <Route
            path="/admin/closure-requests"
            element={<Navigate to="/admin/account-requests" replace />}
          />
          <Route
            path="/admin/audit-logs"
            element={<AdminRoute>{withLayout(<AdminAuditLogs />)}</AdminRoute>}
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
