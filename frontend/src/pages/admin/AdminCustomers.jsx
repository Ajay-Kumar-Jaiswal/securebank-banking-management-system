import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  getAllCustomers,
  getCustomerDetails,
  updateCustomerStatus,
} from "../../api/adminApi";
import {
  extractErrorMessage,
  formatCurrency,
  formatDateTime,
} from "../../utils/errorUtils";
import { useAuth } from "../../context/AuthContext";
import AlertMessage from "../../components/AlertMessage";
import StatusBadge from "../../components/StatusBadge";
import ConfirmModal from "../../components/ConfirmModal";

export default function AdminCustomers() {
  const navigate = useNavigate();
  const { user: currentAdmin } = useAuth();
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(true);

  // Customer Detail Modal state
  const [selectedCustomerId, setSelectedCustomerId] = useState(null);
  const [customerDetails, setCustomerDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [detailsError, setDetailsError] = useState(null);

  // Status Change Confirmation Modal state
  const [statusModal, setStatusModal] = useState({
    isOpen: false,
    user: null,
    newStatus: "",
  });
  const [updatingStatus, setUpdatingStatus] = useState(false);

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
      const res = await getAllCustomers(params);
      setCustomers(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load customers."));
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDetails = async (userId) => {
    setSelectedCustomerId(userId);
    setLoadingDetails(true);
    setDetailsError(null);
    setCustomerDetails(null);
    try {
      const res = await getCustomerDetails(userId);
      setCustomerDetails(res.data);
    } catch (err) {
      setDetailsError(extractErrorMessage(err, "Could not load customer details."));
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleCloseDetails = () => {
    setSelectedCustomerId(null);
    setCustomerDetails(null);
  };

  const promptStatusChange = (user, newStatus) => {
    setError(null);
    setSuccess(null);
    if (user.userId === currentAdmin?.userId && newStatus !== "ACTIVE") {
      setError("You cannot deactivate your own administrator account.");
      return;
    }
    setStatusModal({
      isOpen: true,
      user,
      newStatus,
    });
  };

  const handleConfirmStatusChange = async () => {
    if (!statusModal.user || !statusModal.newStatus) return;
    setUpdatingStatus(true);
    setError(null);
    setSuccess(null);
    try {
      await updateCustomerStatus(statusModal.user.userId, statusModal.newStatus);
      setSuccess(`User ${statusModal.user.fullName} (${statusModal.user.email}) status changed to ${statusModal.newStatus}.`);
      setStatusModal({ isOpen: false, user: null, newStatus: "" });
      await load();
      if (selectedCustomerId === statusModal.user.userId) {
        handleOpenDetails(statusModal.user.userId);
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to update customer status."));
      setStatusModal({ isOpen: false, user: null, newStatus: "" });
    } finally {
      setUpdatingStatus(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Customer Management</h1>

      <div className="card">
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />

        <form onSubmit={load} className="filter-form">
          <label style={{ flex: 1 }}>
            Search Customers
            <input
              placeholder="Search by full name or email address..."
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
              <option value="DEACTIVATED">Deactivated</option>
            </select>
          </label>
          <button className="btn btn-secondary" type="submit">
            Search
          </button>
        </form>
      </div>

      <div className="card">
        {loading ? (
          <p>Loading customers...</p>
        ) : customers.length === 0 ? (
          <p>No customers match the given search criteria.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Full Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((c) => (
                  <tr key={c.userId}>
                    <td>{c.userId}</td>
                    <td><strong>{c.fullName}</strong></td>
                    <td>{c.email}</td>
                    <td>{c.phoneNumber || "—"}</td>
                    <td>
                      <span className="role-tag" style={{ marginLeft: 0 }}>{c.role}</span>
                    </td>
                    <td>
                      <StatusBadge status={c.status} />
                    </td>
                    <td>{formatDateTime(c.createdAt)}</td>
                    <td className="action-cell">
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={() => navigate(`/admin/customers/${c.userId}`)}
                      >
                        Details
                      </button>
                      {currentAdmin && c.userId === currentAdmin.userId ? (
                        <button
                          className="btn btn-sm btn-secondary"
                          disabled
                          title="You cannot deactivate your own administrator account."
                          style={{ opacity: 0.6, cursor: "not-allowed" }}
                        >
                          Protected (Self)
                        </button>
                      ) : (
                        <>
                          {c.status !== "ACTIVE" && (
                            <button
                              className="btn btn-sm btn-primary"
                              onClick={() => promptStatusChange(c, "ACTIVE")}
                            >
                              Reactivate
                            </button>
                          )}
                          {c.status === "ACTIVE" && (
                            <button
                              className="btn btn-sm btn-warning"
                              onClick={() => promptStatusChange(c, "SUSPENDED")}
                            >
                              Suspend
                            </button>
                          )}
                          {c.status !== "DEACTIVATED" && (
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => promptStatusChange(c, "DEACTIVATED")}
                            >
                              Deactivate
                            </button>
                          )}
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Customer Details Modal */}
      {selectedCustomerId && (
        <div className="modal-backdrop" onClick={handleCloseDetails}>
          <div className="modal-box modal-large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">
                Customer Profile: {customerDetails?.user?.fullName || `#${selectedCustomerId}`}
              </h3>
              <button className="modal-close" onClick={handleCloseDetails}>
                &times;
              </button>
            </div>
            <div className="modal-body">
              <AlertMessage message={detailsError} />
              {loadingDetails && <p>Loading customer profile and financial records...</p>}

              {customerDetails && (() => {
                const customer = customerDetails?.customer || customerDetails?.user;
                const customerAccounts = customerDetails?.accounts || [];
                const customerTxs = customerDetails?.recentTransactions || [];
                const customerReqs = customerDetails?.accountRequests || customerDetails?.closureRequests || [];

                if (!customer) return <p>Customer data unavailable.</p>;

                return (
                  <>
                    <div className="detail-grid" style={{ marginBottom: "1.5rem" }}>
                      <div>
                        <div className="detail-label">User ID</div>
                        <div className="detail-value">{customer.userId}</div>
                      </div>
                      <div>
                        <div className="detail-label">Email</div>
                        <div className="detail-value" style={{ fontSize: "1rem" }}>{customer.email}</div>
                      </div>
                      <div>
                        <div className="detail-label">Phone</div>
                        <div className="detail-value" style={{ fontSize: "1rem" }}>{customer.phoneNumber || "—"}</div>
                      </div>
                      <div>
                        <div className="detail-label">Status</div>
                        <div className="detail-value">
                          <StatusBadge status={customer.status} />
                        </div>
                      </div>
                      <div style={{ gridColumn: "span 2" }}>
                        <div className="detail-label">Address</div>
                        <div className="detail-value" style={{ fontSize: "0.95rem" }}>
                          {customer.address || "No address recorded"}
                        </div>
                      </div>
                    </div>

                    <h4>Customer Bank Accounts</h4>
                    {customerAccounts.length === 0 ? (
                      <p style={{ color: "var(--text-muted)" }}>No accounts opened.</p>
                    ) : (
                      <div className="table-container" style={{ marginBottom: "1.5rem" }}>
                        <table className="table">
                          <thead>
                            <tr>
                              <th>Account Number</th>
                              <th>Type</th>
                              <th>Balance</th>
                              <th>Status</th>
                              <th>Opened</th>
                            </tr>
                          </thead>
                          <tbody>
                            {customerAccounts.map((acc) => (
                              <tr key={acc.accountId}>
                                <td><strong>{acc.accountNumber}</strong></td>
                                <td>{acc.accountType}</td>
                                <td>{formatCurrency(acc.balance)}</td>
                                <td>
                                  <StatusBadge status={acc.status} />
                                </td>
                                <td>{formatDateTime(acc.createdAt)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    <h4>Recent Account Transactions</h4>
                    {customerTxs.length === 0 ? (
                      <p style={{ color: "var(--text-muted)" }}>No recent transactions recorded.</p>
                    ) : (
                      <div className="table-container" style={{ marginBottom: "1.5rem" }}>
                        <table className="table">
                          <thead>
                            <tr>
                              <th>Date</th>
                              <th>Reference</th>
                              <th>Type</th>
                              <th>Amount</th>
                              <th>Balance After</th>
                            </tr>
                          </thead>
                          <tbody>
                            {customerTxs.map((tx) => (
                              <tr key={tx.transactionId}>
                                <td>{formatDateTime(tx.createdAt)}</td>
                                <td>{tx.transactionReference}</td>
                                <td>
                                  <StatusBadge status={tx.transactionType} />
                                </td>
                                <td>{formatCurrency(tx.amount)}</td>
                                <td>{formatCurrency(tx.balanceAfter)}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}

                    <h4>Account Closure & Reopen Requests</h4>
                    {customerReqs.length === 0 ? (
                      <p style={{ color: "var(--text-muted)" }}>No requests submitted.</p>
                    ) : (
                      <div className="table-container">
                        <table className="table">
                          <thead>
                            <tr>
                              <th>Type</th>
                              <th>Date</th>
                              <th>Account</th>
                              <th>Reason</th>
                              <th>Status</th>
                              <th>Admin Notes</th>
                            </tr>
                          </thead>
                          <tbody>
                            {customerReqs.map((req) => (
                              <tr key={req.requestId || req.id}>
                                <td>
                                  <span className={`badge ${req.requestType === "REOPEN" ? "badge-primary" : "badge-warning"}`}>
                                    {req.requestType || "CLOSURE"}
                                  </span>
                                </td>
                                <td>{formatDateTime(req.requestedAt)}</td>
                                <td>{req.accountNumber}</td>
                                <td>{req.reason}</td>
                                <td>
                                  <StatusBadge status={req.status} />
                                </td>
                                <td>{req.adminNotes || "—"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </>
                );
              })()}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={handleCloseDetails}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Status Confirmation Modal */}
      <ConfirmModal
        isOpen={statusModal.isOpen}
        title={
          statusModal.user?.role === "ADMIN"
            ? statusModal.newStatus === "DEACTIVATED"
              ? "Deactivate Administrator?"
              : "Activate Administrator?"
            : `Confirm Customer Status: ${statusModal.newStatus}`
        }
        confirmText={
          statusModal.user?.role === "ADMIN"
            ? statusModal.newStatus === "DEACTIVATED"
              ? "Deactivate"
              : "Activate"
            : `Set Status to ${statusModal.newStatus}`
        }
        confirmVariant={statusModal.newStatus === "ACTIVE" ? "primary" : "danger"}
        loading={updatingStatus}
        onCancel={() => setStatusModal({ isOpen: false, user: null, newStatus: "" })}
        onConfirm={handleConfirmStatusChange}
      >
        {statusModal.user?.role === "ADMIN" ? (
          <>
            <div className="confirm-summary">
              <div className="confirm-summary-row">
                <span className="label">Name</span>
                <span className="value">{statusModal.user?.fullName}</span>
              </div>
              <div className="confirm-summary-row">
                <span className="label">Email</span>
                <span className="value">{statusModal.user?.email}</span>
              </div>
              <div className="confirm-summary-row">
                <span className="label">Role</span>
                <span className="value">{statusModal.user?.role}</span>
              </div>
              <div className="confirm-summary-row">
                <span className="label">Target Status</span>
                <span className="value">{statusModal.newStatus}</span>
              </div>
            </div>
            <p className="modal-message">
              {statusModal.newStatus === "DEACTIVATED"
                ? "This administrator will no longer be able to log in."
                : "This administrator will regain access to administrative operations."}
            </p>
            {statusModal.newStatus === "DEACTIVATED" && (
              <div className="warning-callout">
                <strong>Important:</strong> You cannot deactivate the last active administrator. Create or activate another administrator first.
              </div>
            )}
          </>
        ) : (
          <>
            <p className="modal-message">
              Are you sure you want to change the status of <strong>{statusModal.user?.fullName}</strong> ({statusModal.user?.email}) to <strong>{statusModal.newStatus}</strong>?
            </p>
            {statusModal.newStatus === "SUSPENDED" && (
              <div className="warning-callout">
                Suspending this customer prevents them from performing withdrawals, transfers, and new account openings until reactivated.
              </div>
            )}
            {statusModal.newStatus === "DEACTIVATED" && (
              <div className="warning-callout">
                Deactivating this user will revoke their portal access. Financial transaction histories will be securely preserved for compliance auditing.
              </div>
            )}
          </>
        )}
      </ConfirmModal>
    </div>
  );
}
