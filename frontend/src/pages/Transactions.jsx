import { useEffect, useState } from "react";
import { getMyAccounts } from "../api/accountApi";
import { getTransactions } from "../api/transactionApi";
import { extractErrorMessage, formatCurrency, formatDateTime } from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";

export default function Transactions() {
  const [accounts, setAccounts] = useState([]);
  const [accountId, setAccountId] = useState("");
  const [type, setType] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [transactions, setTransactions] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getMyAccounts().then((res) => {
      setAccounts(res.data);
      if (res.data.length > 0) setAccountId(res.data[0].accountId);
    });
  }, []);

  useEffect(() => {
    if (accountId) loadTransactions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accountId]);

  const loadTransactions = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const filters = {};
      if (type) filters.type = type;
      if (from) filters.from = from;
      if (to) filters.to = to;
      const res = await getTransactions(accountId, filters);
      setTransactions(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load transactions."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Transaction History</h1>

      <div className="card">
        <AlertMessage message={error} />
        <form onSubmit={loadTransactions} className="filter-form">
          <label>
            Account
            <select value={accountId} onChange={(e) => setAccountId(e.target.value)}>
              {accounts.map((acc) => (
                <option key={acc.accountId} value={acc.accountId}>
                  {acc.accountNumber}
                </option>
              ))}
            </select>
          </label>
          <label>
            Type
            <select value={type} onChange={(e) => setType(e.target.value)}>
              <option value="">All Types</option>
              <option value="DEPOSIT">Deposit</option>
              <option value="WITHDRAWAL">Withdrawal</option>
              <option value="TRANSFER">All Transfers</option>
              <option value="TRANSFER_IN">Transfer In</option>
              <option value="TRANSFER_OUT">Transfer Out</option>
            </select>
          </label>
          <label>
            From
            <input type="datetime-local" value={from} onChange={(e) => setFrom(e.target.value)} />
          </label>
          <label>
            To
            <input type="datetime-local" value={to} onChange={(e) => setTo(e.target.value)} />
          </label>
          <button type="submit" className="btn btn-secondary">
            Apply Filters
          </button>
        </form>
      </div>

      <div className="card">
        {loading ? (
          <p>Loading...</p>
        ) : transactions.length === 0 ? (
          <p>No transactions found for the selected filters.</p>
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
                  <th>Status</th>
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
                    <td>{tx.status}</td>
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
