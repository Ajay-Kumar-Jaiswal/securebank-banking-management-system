import { useEffect, useState } from "react";
import {
  getAccountRequests,
  approveAccountRequest,
  rejectAccountRequest,
} from "../../api/adminApi";
import {
  extractErrorMessage,
  formatDateTime,
} from "../../utils/errorUtils";
import AlertMessage from "../../components/AlertMessage";
import StatusBadge from "../../components/StatusBadge";
import ConfirmModal from "../../components/ConfirmModal";

export default function AdminAccountRequests() {
  const [requests, setRequests] = useState([]);
  const [typeFilter, setTypeFilter] = useState("ALL"); // ALL | CLOSURE | REOPEN
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(true);

  // Review Modal state
  const [reviewModal, setReviewModal] = useState({
    isOpen: false,
    request: null,
    action: "", // 'approve' | 'reject'
  });
  const [adminNotes, setAdminNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typeFilter, statusFilter]);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (typeFilter !== "ALL") params.request_type = typeFilter;
      const res = await getAccountRequests(params);
      setRequests(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load account requests."));
    } finally {
      setLoading(false);
    }
  };

  const handleOpenReview = (request, action) => {
    const isReopen = request.requestType === "REOPEN";
    if (action === "approve") {
      setAdminNotes(
        isReopen
          ? "Account reopen verified and approved."
          : "Account closure verified and approved."
      );
    } else {
      setAdminNotes("Request declined by administration.");
    }
    setReviewModal({
      isOpen: true,
      request,
      action,
    });
  };

  const handleConfirmReview = async () => {
    if (!reviewModal.request || !reviewModal.action) return;
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    const req = reviewModal.request;
    const reqId = req.requestId || req.id;
    const isReopen = req.requestType === "REOPEN";
    const reqLabel = isReopen ? "Reopen" : "Closure";

    try {
      if (reviewModal.action === "approve") {
        await approveAccountRequest(reqId, adminNotes.trim());
        setSuccess(
          `${reqLabel} request #${reqId} approved. Account ${req.accountNumber} is now ${
            isReopen ? "ACTIVE" : "CLOSED"
          }.`
        );
      } else {
        await rejectAccountRequest(reqId, adminNotes.trim());
        setSuccess(`${reqLabel} request #${reqId} rejected. Account remains unchanged.`);
      }
      setReviewModal({ isOpen: false, request: null, action: "" });
      setAdminNotes("");
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, `Failed to ${reviewModal.action} ${reqLabel.toLowerCase()} request.`));
      setReviewModal({ isOpen: false, request: null, action: "" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <h1 className="page-title" style={{ margin: 0 }}>
          Account Requests
        </h1>
        <button className="btn btn-sm btn-secondary" onClick={load}>
          Refresh List
        </button>
      </div>

      <div className="card">
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />

        {/* Type Filter Tabs: [ All ] [ Closure ] [ Reopen ] */}
        <div style={{ marginBottom: "1rem" }}>
          <div
            style={{
              display: "inline-flex",
              flexWrap: "wrap",
              maxWidth: "100%",
              borderRadius: "6px",
              border: "1px solid var(--border-color, #d1d5db)",
              overflow: "hidden",
              background: "var(--bg-light, #f9fafb)",
            }}
          >
            {[
              { id: "ALL", label: "All Requests" },
              { id: "CLOSURE", label: "Closure Requests" },
              { id: "REOPEN", label: "Reopen Requests" },
            ].map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setTypeFilter(tab.id)}
                style={{
                  padding: "0.5rem 1rem",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "0.88rem",
                  fontWeight: typeFilter === tab.id ? 600 : 400,
                  backgroundColor:
                    typeFilter === tab.id
                      ? "var(--teal-700, #0f5c56)"
                      : "transparent",
                  color: typeFilter === tab.id ? "#ffffff" : "var(--text-color, #374151)",
                  transition: "all 0.15s ease-in-out",
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="filter-form">
          <label>
            Filter by Request Status
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="PENDING">Pending Review</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </label>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p>Loading account requests...</p>
        ) : requests.length === 0 ? (
          <p>No account requests found matching the current filters.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Type</th>
                  <th>Requested</th>
                  <th>Customer</th>
                  <th>Account Number</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Admin Notes</th>
                  <th>Reviewed At</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((req) => {
                  const isReopen = req.requestType === "REOPEN";
                  return (
                    <tr key={req.requestId || req.id}>
                      <td>#{req.requestId || req.id}</td>
                      <td>
                        <span
                          className={`badge ${
                            isReopen ? "badge-primary" : "badge-warning"
                          }`}
                          style={{
                            display: "inline-block",
                            padding: "0.2rem 0.55rem",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                            letterSpacing: "0.02em",
                            backgroundColor: isReopen
                              ? "var(--teal-100, #ccfbf1)"
                              : "var(--amber-100, #fef3c7)",
                            color: isReopen
                              ? "var(--teal-800, #115e59)"
                              : "var(--amber-800, #92400e)",
                          }}
                        >
                          {req.requestType || "CLOSURE"}
                        </span>
                      </td>
                      <td>{formatDateTime(req.requestedAt)}</td>
                      <td>
                        <strong>{req.customerName}</strong>
                        <div
                          style={{
                            fontSize: "0.8rem",
                            color: "var(--text-muted)",
                          }}
                        >
                          {req.customerEmail}
                        </div>
                      </td>
                      <td>
                        <strong>{req.accountNumber}</strong>
                      </td>
                      <td>
                        <div>{req.reason}</div>
                        {req.additionalNotes && (
                          <div
                            style={{
                              fontSize: "0.8rem",
                              color: "var(--text-muted)",
                              marginTop: "0.2rem",
                            }}
                          >
                            Note: {req.additionalNotes}
                          </div>
                        )}
                      </td>
                      <td>
                        <StatusBadge status={req.status} />
                      </td>
                      <td>{req.adminNotes || "—"}</td>
                      <td>
                        {req.reviewedAt
                          ? formatDateTime(req.reviewedAt)
                          : "—"}
                      </td>
                      <td className="action-cell">
                        {req.status === "PENDING" ? (
                          <>
                            <button
                              className="btn btn-sm btn-primary"
                              onClick={() => handleOpenReview(req, "approve")}
                            >
                              Approve
                            </button>
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => handleOpenReview(req, "reject")}
                            >
                              Reject
                            </button>
                          </>
                        ) : (
                          <span
                            style={{
                              fontSize: "0.82rem",
                              color: "var(--text-muted)",
                            }}
                          >
                            Resolved
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Approve / Reject Modal with Admin Notes */}
      <ConfirmModal
        isOpen={reviewModal.isOpen}
        title={
          reviewModal.action === "approve"
            ? reviewModal.request?.requestType === "REOPEN"
              ? "Approve Account Reopen"
              : "Approve Account Closure"
            : `Reject ${
                reviewModal.request?.requestType === "REOPEN"
                  ? "Account Reopen"
                  : "Account Closure"
              } Request`
        }
        confirmText={
          reviewModal.action === "approve"
            ? reviewModal.request?.requestType === "REOPEN"
              ? "Approve & Reopen Account"
              : "Approve & Close Account"
            : "Reject Request"
        }
        confirmVariant={reviewModal.action === "approve" ? "primary" : "danger"}
        loading={submitting}
        onCancel={() =>
          setReviewModal({ isOpen: false, request: null, action: "" })
        }
        onConfirm={handleConfirmReview}
      >
        <div className="confirm-summary">
          <div className="confirm-summary-row">
            <span className="label">Request Type</span>
            <span className="value">
              <strong>{reviewModal.request?.requestType || "CLOSURE"}</strong>
            </span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Request ID</span>
            <span className="value">
              #{reviewModal.request?.requestId || reviewModal.request?.id}
            </span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Account Number</span>
            <span className="value">{reviewModal.request?.accountNumber}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Customer</span>
            <span className="value">{reviewModal.request?.customerName}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Customer Reason</span>
            <span className="value">{reviewModal.request?.reason}</span>
          </div>
        </div>

        <p className="modal-message">
          {reviewModal.action === "approve"
            ? reviewModal.request?.requestType === "REOPEN"
              ? "Approving this request will immediately restore the account to ACTIVE status, allowing customer deposits, withdrawals, and transfers."
              : "Approving this request will immediately mark the account as CLOSED and create a formal audit trail. Customer balance must be zero."
            : "Rejecting this request will keep the account in its current status."}
        </p>

        <label style={{ display: "block", marginBottom: "0.5rem" }}>
          Admin Decision Notes
          <textarea
            rows={3}
            value={adminNotes}
            onChange={(e) => setAdminNotes(e.target.value)}
            placeholder="Provide context or instructions for the record..."
          />
        </label>
      </ConfirmModal>
    </div>
  );
}
