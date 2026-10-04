import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { getMyAccounts } from "../api/accountApi";
import { getTransactions } from "../api/transactionApi";
import { useAuth } from "../context/AuthContext";
import { extractErrorMessage, formatCurrency, formatDateTime } from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";
import StatusBadge from "../components/StatusBadge";

export default function Dashboard() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const accountsRes = await getMyAccounts();
      const accountsList = accountsRes.data;
      setAccounts(accountsList);

      if (accountsList.length > 0) {
        const txPromises = accountsList.map((acc) => getTransactions(acc.accountId));
        const txResults = await Promise.all(txPromises);
        const allTx = txResults.flatMap((r) => r.data);
        allTx.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
        setRecentTransactions(allTx.slice(0, 8));
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load your dashboard."));
    } finally {
      setLoading(false);
    }
  };

  const totalBalance = useMemo(
    () => accounts.reduce((sum, a) => sum + Number(a.balance), 0),
    [accounts]
  );

  const deposits = recentTransactions.filter((t) => t.transactionType === "DEPOSIT").length;
  const withdrawals = recentTransactions.filter((t) => t.transactionType === "WITHDRAWAL").length;
  const transfers = recentTransactions.filter((t) => t.transactionType?.startsWith("TRANSFER")).length;

  return (
    <div className="page">
      <h1 className="page-title">Welcome back, {user?.fullName?.split(" ")[0]}</h1>

      <AlertMessage message={error} />

      {loading ? (
        <p>Loading your dashboard...</p>
      ) : (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <div className="stat-label">Total Balance</div>
              <div className="stat-value">{formatCurrency(totalBalance)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Accounts</div>
              <div className="stat-value">{accounts.length}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Deposits (recent)</div>
              <div className="stat-value">{deposits}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Withdrawals (recent)</div>
              <div className="stat-value">{withdrawals}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Transfers (recent)</div>
              <div className="stat-value">{transfers}</div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <h2>My Accounts</h2>
              <Link className="btn btn-secondary" to="/accounts">
                View all
              </Link>
            </div>
            {accounts.length === 0 ? (
              <p>You don't have any accounts yet. Open one from the Accounts page.</p>
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Account Number</th>
                      <th>Type</th>
                      <th>Balance</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accounts.map((acc) => (
                      <tr key={acc.accountId}>
                        <td>
                          <Link to={`/accounts/${acc.accountId}`}>{acc.accountNumber}</Link>
                        </td>
                        <td>{acc.accountType}</td>
                        <td>{formatCurrency(acc.balance)}</td>
                        <td>
                          <StatusBadge status={acc.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="card">
            <div className="card-header">
              <h2>Recent Transactions</h2>
              <Link className="btn btn-secondary" to="/transactions">
                View all
              </Link>
            </div>
            {recentTransactions.length === 0 ? (
              <p>No transactions yet.</p>
            ) : (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type</th>
                      <th>Account</th>
                      <th>Amount</th>
                      <th>Balance After</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentTransactions.map((tx) => (
                      <tr key={tx.transactionId}>
                        <td>{formatDateTime(tx.createdAt)}</td>
                        <td>{tx.transactionType}</td>
                        <td>{tx.accountNumber}</td>
                        <td>{formatCurrency(tx.amount)}</td>
                        <td>{formatCurrency(tx.balanceAfter)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
