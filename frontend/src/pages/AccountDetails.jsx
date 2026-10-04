import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getAccountDetails } from "../api/accountApi";
import { getTransactions } from "../api/transactionApi";
import { extractErrorMessage, formatCurrency, formatDateTime } from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";
import StatusBadge from "../components/StatusBadge";

export default function AccountDetails() {
  const { id } = useParams();
  const [account, setAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [accRes, txRes] = await Promise.all([
        getAccountDetails(id),
        getTransactions(id),
      ]);
      setAccount(accRes.data);
      setTransactions(txRes.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load account details."));
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="page">Loading...</div>;

  return (
    <div className="page">
      <h1 className="page-title">Account Details</h1>
      <AlertMessage message={error} />

      {account && (
        <div className="card">
          <div className="detail-grid">
            <div>
              <div className="detail-label">Account Number</div>
              <div className="detail-value">{account.accountNumber}</div>
            </div>
            <div>
              <div className="detail-label">Type</div>
              <div className="detail-value">{account.accountType}</div>
            </div>
            <div>
              <div className="detail-label">Balance</div>
              <div className="detail-value">{formatCurrency(account.balance)}</div>
            </div>
            <div>
              <div className="detail-label">Status</div>
              <div className="detail-value">
                <StatusBadge status={account.status} />
              </div>
            </div>
          </div>
          <div className="action-row">
            <Link className="btn btn-primary" to="/deposit">
              Deposit
            </Link>
            <Link className="btn btn-primary" to="/withdraw">
              Withdraw
            </Link>
            <Link className="btn btn-primary" to="/transfer">
              Transfer
            </Link>
            <Link className="btn btn-secondary" to={`/account-closure?accountId=${account.accountId}`}>
              Request Closure
            </Link>
          </div>

        </div>
      )}

      <div className="card">
        <h2>Transaction History</h2>
        {transactions.length === 0 ? (
          <p>No transactions for this account yet.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Reference</th>
                  <th>Type</th>
                  <th>Description</th>
                  <th>Amount</th>
                  <th>Balance After</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.transactionId}>
                    <td>{formatDateTime(tx.createdAt)}</td>
                    <td>{tx.transactionReference}</td>
                    <td>{tx.transactionType}</td>
                    <td>{tx.description}</td>
                    <td>{formatCurrency(tx.amount)}</td>
                    <td>{formatCurrency(tx.balanceAfter)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
