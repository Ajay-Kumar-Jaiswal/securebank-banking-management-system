import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboardMetrics } from "../../api/adminApi";
import { extractErrorMessage, formatCurrency, formatDateTime } from "../../utils/errorUtils";
import AlertMessage from "../../components/AlertMessage";
import StatusBadge from "../../components/StatusBadge";

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getDashboardMetrics();
      setData(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load admin dashboard metrics."));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <h1 className="page-title">Admin Dashboard</h1>
        <p>Loading administrative telemetry...</p>
      </div>
    );
  }

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h1 className="page-title" style={{ margin: 0 }}>Executive Admin Dashboard</h1>
        <button className="btn btn-sm btn-secondary" onClick={load}>
          Refresh Metrics
        </button>
      </div>

      <AlertMessage message={error} />

      {data && (
        <>
          {/* Main Financial & Entity Counters */}
          <div className="stat-grid" style={{ marginBottom: "1.5rem" }}>
            <div className="stat-card">
              <div className="stat-label">Total Customers</div>
              <div className="stat-value">{data.totalCustomers}</div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                <span style={{ color: "var(--teal-700)", fontWeight: 600 }}>{data.activeCustomers} active</span>
                {" · "}
                <span style={{ color: "var(--gold-600)", fontWeight: 600 }}>{data.suspendedCustomers} suspended</span>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Bank Accounts</div>
              <div className="stat-value">{data.totalAccounts}</div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                <span style={{ color: "var(--teal-700)", fontWeight: 600 }}>{data.activeAccounts} active</span>
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Pending Closures</div>
              <div className="stat-value" style={{ color: data.pendingClosureRequests > 0 ? "var(--red-700)" : "inherit" }}>
                {data.pendingClosureRequests}
              </div>
              <div style={{ fontSize: "0.8rem", marginTop: "0.25rem" }}>
                {data.pendingClosureRequests > 0 ? (
                  <Link to="/admin/closure-requests" style={{ color: "var(--red-700)", fontWeight: 600 }}>
                    Requires Review &rarr;
                  </Link>
                ) : (
                  <span style={{ color: "var(--text-muted)" }}>Up to date</span>
                )}
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Total Custodial Balance</div>
              <div className="stat-value" style={{ color: "var(--teal-700)" }}>
                {formatCurrency(data.bankWideBalance)}
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
                Across all accounts
              </div>
            </div>
          </div>

          {/* Transaction Volume Counters */}
          <div className="stat-grid" style={{ marginBottom: "2rem" }}>
            <div className="stat-card">
              <div className="stat-label">Total Deposits</div>
              <div className="stat-value" style={{ fontSize: "1.4rem" }}>
                {formatCurrency(data.totalDepositsAmount)}
              </div>
              <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                {data.totalDepositsCount} completed deposits
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Total Withdrawals</div>
              <div className="stat-value" style={{ fontSize: "1.4rem" }}>
                {formatCurrency(data.totalWithdrawalsAmount)}
              </div>
              <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                {data.totalWithdrawalsCount} completed withdrawals
              </div>
            </div>

            <div className="stat-card">
              <div className="stat-label">Total Transfers</div>
              <div className="stat-value" style={{ fontSize: "1.4rem" }}>
                {formatCurrency(data.totalTransfersAmount)}
              </div>
              <div style={{ fontSize: "0.82rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                {data.totalTransfersCount} intra-bank transfers
              </div>
            </div>
          </div>

          <div className="dashboard-two-col">
            {/* Recent Transactions */}
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h2>Recent Transactions</h2>
                <Link to="/admin/transactions" className="btn btn-sm btn-ghost">
                  View All &rarr;
                </Link>
              </div>

              {(!data.recentTransactions || data.recentTransactions.length === 0) ? (
                <p>No recent transactions.</p>
              ) : (
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Account</th>
                        <th>Type</th>
                        <th>Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recentTransactions.slice(0, 8).map((tx) => (
                        <tr key={tx.transactionId}>
                          <td>{formatDateTime(tx.createdAt)}</td>
                          <td>{tx.accountNumber}</td>
                          <td>
                            <StatusBadge status={tx.transactionType} />
                          </td>
                          <td>{formatCurrency(tx.amount)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Recent Customers */}
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.75rem" }}>
                <h2>Recent Customer Signups</h2>
                <Link to="/admin/customers" className="btn btn-sm btn-ghost">
                  Manage Customers &rarr;
                </Link>
              </div>

              {(!data.recentCustomers || data.recentCustomers.length === 0) ? (
                <p>No recent customer registrations.</p>
              ) : (
                <div className="table-container">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Status</th>
                        <th>Joined</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recentCustomers.slice(0, 8).map((c) => (
                        <tr key={c.userId}>
                          <td>{c.fullName}</td>
                          <td>{c.email}</td>
                          <td>
                            <StatusBadge status={c.status} />
                          </td>
                          <td>{formatDateTime(c.createdAt)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
