import { useEffect, useState } from "react";
import { getAllTransactions } from "../../api/adminApi";
import { extractErrorMessage, formatCurrency, formatDateTime } from "../../utils/errorUtils";
import AlertMessage from "../../components/AlertMessage";
import StatusBadge from "../../components/StatusBadge";

export default function AdminTransactions() {
  const [transactions, setTransactions] = useState([]);
  const [typeFilter, setTypeFilter] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAllTransactions(typeFilter);
      setTransactions(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load transactions."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h1 className="page-title" style={{ margin: 0 }}>All Transactions</h1>
        <button className="btn btn-sm btn-secondary" onClick={load}>
          Refresh
        </button>
      </div>

      <div className="card">
        <AlertMessage message={error} />
        <div className="filter-form">
          <label>
            Filter by Transaction Type
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="">All Types</option>
              <option value="DEPOSIT">Deposit</option>
              <option value="WITHDRAWAL">Withdrawal</option>
              <option value="TRANSFER_IN">Transfer In</option>
              <option value="TRANSFER_OUT">Transfer Out</option>
            </select>
          </label>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p>Loading transactions...</p>
        ) : transactions.length === 0 ? (
          <p>No transactions found matching the filter.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Date & Time</th>
                  <th>Reference</th>
                  <th>Account</th>
                  <th>Type</th>
                  <th>Amount</th>
                  <th>Balance Before</th>
                  <th>Balance After</th>
                  <th>Description</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((tx) => (
                  <tr key={tx.transactionId}>
                    <td>{formatDateTime(tx.createdAt)}</td>
                    <td>
                      <span style={{ fontFamily: "monospace", fontSize: "0.85rem" }}>
                        {tx.transactionReference}
                      </span>
                    </td>
                    <td><strong>{tx.accountNumber}</strong></td>
                    <td>
                      <StatusBadge status={tx.transactionType} />
                    </td>
                    <td>
                      <strong style={{
                        color: tx.transactionType === "DEPOSIT" || tx.transactionType === "TRANSFER_IN"
                          ? "var(--teal-700)"
                          : "var(--red-700)"
                      }}>
                        {tx.transactionType === "DEPOSIT" || tx.transactionType === "TRANSFER_IN" ? "+" : "-"}
                        {formatCurrency(tx.amount)}
                      </strong>
                    </td>
                    <td>{formatCurrency(tx.balanceBefore)}</td>
                    <td>{formatCurrency(tx.balanceAfter)}</td>
                    <td>{tx.description || "—"}</td>
                    <td>
                      <StatusBadge status={tx.status} />
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
