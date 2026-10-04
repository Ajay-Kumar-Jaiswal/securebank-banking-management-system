import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyAccounts, createAccount } from "../api/accountApi";
import { extractErrorMessage, formatCurrency } from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";
import StatusBadge from "../components/StatusBadge";

export default function Accounts() {
  const [accounts, setAccounts] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [accountType, setAccountType] = useState("SAVINGS");
  const [creating, setCreating] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    setLoading(true);
    try {
      const res = await getMyAccounts();
      setAccounts(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load your accounts."));
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setCreating(true);
    try {
      await createAccount(accountType);
      setSuccess(`New ${accountType} account created successfully.`);
      await loadAccounts();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not create a new account."));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">My Accounts</h1>

      <div className="card">
        <h2>Open a New Account</h2>
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />
        <form onSubmit={handleCreate} className="inline-form">
          <label>
            Account Type
            <select value={accountType} onChange={(e) => setAccountType(e.target.value)}>
              <option value="SAVINGS">Savings</option>
              <option value="CURRENT">Current</option>
            </select>
          </label>
          <button type="submit" className="btn btn-primary" disabled={creating}>
            {creating ? "Creating..." : "Open Account"}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>All Accounts</h2>
        {loading ? (
          <p>Loading...</p>
        ) : accounts.length === 0 ? (
          <p>You don't have any accounts yet.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Account Number</th>
                  <th>Type</th>
                  <th>Balance</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((acc) => (
                  <tr key={acc.accountId}>
                    <td>{acc.accountNumber}</td>
                    <td>{acc.accountType}</td>
                    <td>{formatCurrency(acc.balance)}</td>
                    <td>
                      <StatusBadge status={acc.status} />
                    </td>
                    <td>
                      <Link className="btn btn-secondary btn-sm" to={`/accounts/${acc.accountId}`}>
                        View Details
                      </Link>
                    </td>
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
