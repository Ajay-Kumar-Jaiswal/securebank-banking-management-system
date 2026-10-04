import { useEffect, useState } from "react";
import { getAllAccounts, updateAccountStatus } from "../../api/adminApi";
import { extractErrorMessage, formatCurrency, formatDateTime } from "../../utils/errorUtils";
import AlertMessage from "../../components/AlertMessage";
import StatusBadge from "../../components/StatusBadge";
import ConfirmModal from "../../components/ConfirmModal";

export default function AdminAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(true);

  // Status Change Confirmation Modal state
  const [statusModal, setStatusModal] = useState({
    isOpen: false,
    account: null,
    newStatus: "",
  });
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const load = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (statusFilter) params.status = statusFilter;
      const res = await getAllAccounts(params);
      setAccounts(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load accounts."));
    } finally {
      setLoading(false);
    }
  };

  const promptStatusChange = (account, newStatus) => {
    setStatusModal({
      isOpen: true,
      account,
      newStatus,
    });
  };

  const handleConfirmStatusChange = async () => {
    if (!statusModal.account || !statusModal.newStatus) return;
    setUpdating(true);
    setError(null);
    setSuccess(null);
    try {
      await updateAccountStatus(statusModal.account.accountId, statusModal.newStatus);
      setSuccess(`Account ${statusModal.account.accountNumber} status updated to ${statusModal.newStatus}.`);
      setStatusModal({ isOpen: false, account: null, newStatus: "" });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not update account status."));
      setStatusModal({ isOpen: false, account: null, newStatus: "" });
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Account Management</h1>

      <div className="card">
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />

        <form onSubmit={load} className="filter-form">
          <label style={{ flex: 1 }}>
            Search Accounts
            <input
              placeholder="Search by account number or customer name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </label>
          <label>
            Status
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">Suspended</option>
              <option value="CLOSED">Closed</option>
              <option value="PENDING">Pending</option>
            </select>
          </label>
          <button className="btn btn-secondary" type="submit">
            Search
          </button>
        </form>
      </div>

      <div className="card">
        {loading ? (
          <p>Loading accounts...</p>
        ) : accounts.length === 0 ? (
          <p>No accounts found matching the criteria.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Account Number</th>
                  <th>Customer</th>
                  <th>Type</th>
                  <th>Balance</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {accounts.map((acc) => (
                  <tr key={acc.accountId}>
                    <td><strong>{acc.accountNumber}</strong></td>
                    <td>{acc.customerName}</td>
                    <td>{acc.accountType}</td>
                    <td><strong>{formatCurrency(acc.balance)}</strong></td>
                    <td>
                      <StatusBadge status={acc.status} />
                    </td>
                    <td>{formatDateTime(acc.createdAt)}</td>
                    <td className="action-cell">
                      {acc.status !== "ACTIVE" && (
                        <button
                          className="btn btn-sm btn-primary"
                          onClick={() => promptStatusChange(acc, "ACTIVE")}
                        >
                          Activate
                        </button>
                      )}
                      {acc.status === "ACTIVE" && (
                        <button
                          className="btn btn-sm btn-warning"
                          onClick={() => promptStatusChange(acc, "SUSPENDED")}
                        >
                          Suspend
                        </button>
                      )}
                      {acc.status !== "CLOSED" && (
                        <button
                          className="btn btn-sm btn-danger"
                          onClick={() => promptStatusChange(acc, "CLOSED")}
                        >
                          Close
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={statusModal.isOpen}
        title={`Confirm Account Status: ${statusModal.newStatus}`}
        confirmText={`Set to ${statusModal.newStatus}`}
        confirmVariant={statusModal.newStatus === "ACTIVE" ? "primary" : "danger"}
        loading={updating}
        onCancel={() => setStatusModal({ isOpen: false, account: null, newStatus: "" })}
        onConfirm={handleConfirmStatusChange}
      >
        <div className="confirm-summary">
          <div className="confirm-summary-row">
            <span className="label">Account Number</span>
            <span className="value">{statusModal.account?.accountNumber}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Customer</span>
            <span className="value">{statusModal.account?.customerName}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Current Balance</span>
            <span className="value">{formatCurrency(statusModal.account?.balance || 0)}</span>
          </div>
        </div>
        <p className="modal-message">
          Are you sure you want to change the status of this account to <strong>{statusModal.newStatus}</strong>?
        </p>
        {statusModal.newStatus === "CLOSED" && Number(statusModal.account?.balance) > 0 && (
          <div className="warning-callout">
            <strong>Warning:</strong> This account holds an active balance of {formatCurrency(statusModal.account?.balance)}. Please ensure remaining funds are properly settled before administrative closure.
          </div>
        )}
      </ConfirmModal>
    </div>
  );
}
