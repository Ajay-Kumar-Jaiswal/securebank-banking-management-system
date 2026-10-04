import { useState, useEffect } from "react";
import { NavLink, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout, isAdmin } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [lastPath, setLastPath] = useState(location.pathname);

  // Close drawer whenever the route changes
  if (location.pathname !== lastPath) {
    setLastPath(location.pathname);
    if (drawerOpen) {
      setDrawerOpen(false);
    }
  }

  // Close drawer on Escape key press for accessibility
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && drawerOpen) {
        setDrawerOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [drawerOpen]);

  // Prevent background scroll when mobile drawer is open
  useEffect(() => {
    if (drawerOpen) {
      document.body.classList.add("drawer-open");
    } else {
      document.body.classList.remove("drawer-open");
    }
    return () => {
      document.body.classList.remove("drawer-open");
    };
  }, [drawerOpen]);

  const handleLogout = () => {
    setDrawerOpen(false);
    logout();
    navigate("/login");
  };

  if (!user) return null;

  const customerLinks = [
    { to: "/dashboard", label: "Dashboard" },
    { to: "/accounts", label: "My Accounts" },
    { to: "/transfer", label: "Transfer" },
    { to: "/deposit", label: "Deposit" },
    { to: "/withdraw", label: "Withdraw" },
    { to: "/transactions", label: "Transactions" },
    { to: "/beneficiaries", label: "Beneficiaries" },
    { to: "/account-closure", label: "Account Requests" },
    { to: "/profile", label: "Profile" },
  ];

  const adminLinks = [
    { to: "/admin", label: "Dashboard" },
    { to: "/admin/customers", label: "Customers" },
    { to: "/admin/administrators", label: "Admin Management" },
    { to: "/admin/accounts", label: "Accounts" },
    { to: "/admin/transactions", label: "Transactions" },
    { to: "/admin/account-requests", label: "Account Requests" },
    { to: "/admin/audit-logs", label: "Audit Logs" },
    { to: "/profile", label: "Profile" },
  ];

  const links = isAdmin ? adminLinks : customerLinks;

  return (
    <>
      <nav className="navbar" aria-label="Main Navigation">
        {/* Mobile hamburger button */}
        <button
          type="button"
          className="navbar-toggle"
          onClick={() => setDrawerOpen(true)}
          aria-label="Open navigation"
          aria-expanded={drawerOpen}
        >
          <span className="navbar-toggle-icon" aria-hidden="true">&#9776;</span>
        </button>

        {/* Brand */}
        <div className="navbar-brand">
          SecureBank {isAdmin && <span className="badge-admin">Admin Portal</span>}
        </div>

        {/* Desktop Navigation Links */}
        <div className="navbar-links">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/admin" || link.to === "/dashboard"}
              className={({ isActive }) => "navbar-link" + (isActive ? " active" : "")}
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        {/* User Info & Logout (Desktop / Tablet) */}
        <div className="navbar-user">
          <span className="navbar-username">
            {user.fullName} {isAdmin && <span className="role-tag">ADMIN</span>}
          </span>
          <button className="btn btn-ghost navbar-logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      {/* Mobile Backdrop Overlay */}
      <div
        className={`drawer-backdrop ${drawerOpen ? "open" : ""}`}
        onClick={() => setDrawerOpen(false)}
        aria-hidden="true"
      />

      {/* Mobile Drawer / Sidebar */}
      <aside
        className={`mobile-drawer ${drawerOpen ? "open" : ""}`}
        role="dialog"
        aria-label="Navigation drawer"
        aria-modal={drawerOpen}
      >
        <div className="drawer-header">
          <div className="drawer-brand">
            SecureBank {isAdmin && <span className="badge-admin">Admin</span>}
          </div>
          <button
            type="button"
            className="drawer-close"
            onClick={() => setDrawerOpen(false)}
            aria-label="Close navigation"
          >
            &times;
          </button>
        </div>

        <div className="drawer-user-info">
          <div className="drawer-user-name">{user.fullName}</div>
          <div className="drawer-user-role">
            <span className="role-tag">{isAdmin ? "ADMIN" : "CUSTOMER"}</span>
          </div>
        </div>

        <div className="drawer-links">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/admin" || link.to === "/dashboard"}
              onClick={() => setDrawerOpen(false)}
              className={({ isActive }) => "drawer-link" + (isActive ? " active" : "")}
            >
              {link.label}
            </NavLink>
          ))}
        </div>

        <div className="drawer-footer">
          <button
            type="button"
            className="btn btn-danger drawer-logout-btn"
            onClick={handleLogout}
          >
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}
