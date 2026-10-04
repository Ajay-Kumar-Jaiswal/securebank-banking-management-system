import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { getMyAccounts } from "../api/accountApi";
import {
  createClosureRequest,
  createReopenRequest,
  getMyAccountRequests,
} from "../api/closureApi";
import {
  extractErrorMessage,
  formatCurrency,
  formatDateTime,
} from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";
import StatusBadge from "../components/StatusBadge";
import ConfirmModal from "../components/ConfirmModal";

export default function AccountClosure() {
  const [searchParams] = useSearchParams();
  const preselectedId = searchParams.get("accountId");

  const [accounts, setAccounts] = useState([]);
  const [selectedAccountId, setSelectedAccountId] = useState(preselectedId || "");
  const [reason, setReason] = useState("");
  const [additionalNotes, setAdditionalNotes] = useState("");
  const [confirmed, setConfirmed] = useState(false);

  const [accountRequests, setAccountRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [accRes, reqRes] = await Promise.all([
        getMyAccounts(),
        getMyAccountRequests(),
      ]);
      setAccounts(accRes.data);
      setAccountRequests(reqRes.data);

      if (!selectedAccountId && accRes.data.length > 0) {
        setSelectedAccountId(String(accRes.data[0].accountId));
      } else if (preselectedId) {
        setSelectedAccountId(String(preselectedId));
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Failed to load account requests data."));
    } finally {
      setLoading(false);
    }
  };

  const selectedAccount = accounts.find(
    (a) => String(a.accountId) === String(selectedAccountId)
  );

  const isClosed = selectedAccount && selectedAccount.status === "CLOSED";
  const isActive = selectedAccount && selectedAccount.status === "ACTIVE";
  const isSuspended = selectedAccount && selectedAccount.status === "SUSPENDED";
  const hasNonZeroBalance = selectedAccount && Number(selectedAccount.balance) > 0;

  const mode = isClosed ? "REOPEN" : "CLOSURE";

  const handleOpenConfirm = (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!selectedAccount) {
      setError("Please select an account.");
      return;
    }

    if (mode === "CLOSURE") {
      if (!isActive) {
        setError(`Only ACTIVE accounts can be closed. Current status: ${selectedAccount.status}.`);
        return;
      }
      if (hasNonZeroBalance) {
        setError("Please withdraw or transfer your remaining balance before requesting account closure.");
        return;
      }
    } else {
      if (!isClosed) {
        setError("Only CLOSED accounts can be requested to reopen.");
        return;
      }
    }

    if (!reason.trim()) {
      setError(`Please provide a reason for requesting ${mode === "REOPEN" ? "reopening" : "closure"}.`);
      return;
    }
    if (!confirmed) {
      setError("Please check the confirmation box.");
      return;
    }

    setShowConfirmModal(true);
  };

  const handleConfirmSubmit = async () => {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const payload = {
        accountId: Number(selectedAccountId),
        reason: reason.trim(),
        additionalNotes: additionalNotes.trim() || undefined,
        confirmationCheckbox: true,
      };

      if (mode === "REOPEN") {
        await createReopenRequest(payload);
        setSuccess("Your account reopen request has been submitted for administrative review.");
      } else {
        await createClosureRequest(payload);
        setSuccess("Your account closure request has been submitted for administrative review.");
      }

      setReason("");
      setAdditionalNotes("");
      setConfirmed(false);
      setShowConfirmModal(false);

      // Refresh requests list
      const reqRes = await getMyAccountRequests();
      setAccountRequests(reqRes.data);
    } catch (err) {
      setError(extractErrorMessage(err, `Could not submit ${mode.toLowerCase()} request.`));
      setShowConfirmModal(false);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Account Requests</h1>

      <div className="card card-narrow">
        <h2>
          {mode === "REOPEN" ? "Request Account Reopening" : "Request Account Closure"}
        </h2>
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />

        {loading ? (
          <p>Loading accounts...</p>
        ) : accounts.length === 0 ? (
          <p>You do not have any accounts.</p>
        ) : (
          <form onSubmit={handleOpenConfirm} className="auth-form">
            <label>
              Select Account
              <select
                value={selectedAccountId}
                onChange={(e) => {
                  setSelectedAccountId(e.target.value);
                  setConfirmed(false);
                  setReason("");
                  setAdditionalNotes("");
                }}
                required
              >
                {accounts.map((acc) => (
                  <option key={acc.accountId} value={acc.accountId}>
                    {acc.accountNumber} ({acc.accountType}) — {formatCurrency(acc.balance)} [{acc.status}]
                  </option>
                ))}
              </select>
            </label>

            {mode === "CLOSURE" && hasNonZeroBalance && (
              <div className="warning-callout">
                <strong>Notice:</strong> Please withdraw or transfer your remaining balance before requesting account closure.
                <br />
                Current balance: <strong>{formatCurrency(selectedAccount.balance)}</strong>
                <div style={{ marginTop: "0.5rem" }}>
                  <Link to="/withdraw" className="btn btn-sm btn-secondary" style={{ marginRight: "0.5rem" }}>
                    Go to Withdraw
                  </Link>
                  <Link to="/transfer" className="btn btn-sm btn-secondary">
                    Go to Transfer
                  </Link>
                </div>
              </div>
            )}

            {isClosed && (
              <div
                style={{
                  padding: "0.75rem 1rem",
                  borderRadius: "6px",
                  backgroundColor: "var(--teal-50, #f0fdfa)",
                  border: "1px solid var(--teal-200, #99f6e4)",
                  color: "var(--teal-900, #134e4a)",
                  marginBottom: "1rem",
                  fontSize: "0.9rem",
                }}
              >
                <strong>Account is CLOSED:</strong> You can submit a request to bank administration to reopen this account and restore its operations.
              </div>
            )}

            {isSuspended && (
              <div className="warning-callout">
                <strong>Notice:</strong> This account is currently SUSPENDED. Please contact bank administration directly to resolve account holds.
              </div>
            )}

            <label>
              Reason for {mode === "REOPEN" ? "Reopening" : "Closure"}{" "}
              <span style={{ color: "var(--red-700, #b91c1c)" }}>*</span>
              <input
                type="text"
                placeholder={
                  mode === "REOPEN"
                    ? "e.g. Resuming personal savings, Need account for salary deposits..."
                    : "e.g. Switching banks, No longer needed, Relocating..."
                }
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                required
                disabled={(mode === "CLOSURE" && hasNonZeroBalance) || isSuspended}
              />
            </label>

            <label>
              Additional Notes (optional)
              <textarea
                rows={3}
                placeholder="Any further details or context for bank administration..."
                value={additionalNotes}
                onChange={(e) => setAdditionalNotes(e.target.value)}
                disabled={(mode === "CLOSURE" && hasNonZeroBalance) || isSuspended}
              />
            </label>

            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={confirmed}
                onChange={(e) => setConfirmed(e.target.checked)}
                disabled={(mode === "CLOSURE" && hasNonZeroBalance) || isSuspended}
              />
              <span>
                {mode === "REOPEN"
                  ? "I confirm that I want to request reopening this account and understand that upon admin approval, it will return to ACTIVE status."
                  : "I confirm that I want to request closure for this account and understand that once approved, all account operations will be terminated."}
              </span>
            </label>

            <button
              type="submit"
              className={`btn ${mode === "REOPEN" ? "btn-primary" : "btn-danger"}`}
              disabled={
                submitting ||
                (mode === "CLOSURE" && hasNonZeroBalance) ||
                isSuspended ||
                !confirmed ||
                !reason.trim()
              }
            >
              {mode === "REOPEN" ? "Request Account Reopen" : "Request Account Closure"}
            </button>
          </form>
        )}
      </div>

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={showConfirmModal}
        title={mode === "REOPEN" ? "Confirm Account Reopen Request" : "Confirm Account Closure Request"}
        confirmText={mode === "REOPEN" ? "Submit Reopen Request" : "Submit Closure Request"}
        confirmVariant={mode === "REOPEN" ? "primary" : "danger"}
        loading={submitting}
        onCancel={() => setShowConfirmModal(false)}
        onConfirm={handleConfirmSubmit}
      >
        <div className="confirm-summary">
          <div className="confirm-summary-row">
            <span className="label">Account Number</span>
            <span className="value">{selectedAccount?.accountNumber}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Account Type</span>
            <span className="value">{selectedAccount?.accountType}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Current Balance</span>
            <span className="value">{formatCurrency(selectedAccount?.balance || 0)}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Request Type</span>
            <span className="value">
              <strong>{mode}</strong>
            </span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Reason</span>
            <span className="value">{reason}</span>
          </div>
        </div>
        <p className="modal-message">
          Are you sure you want to submit this {mode.toLowerCase()} request? It will be sent to bank administration for review.
        </p>
      </ConfirmModal>

      {/* Account Requests History */}
      <div className="card" style={{ marginTop: "2rem" }}>
        <h2>My Account Requests</h2>
        {accountRequests.length === 0 ? (
          <p>No account requests submitted yet.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Request ID</th>
                  <th>Type</th>
                  <th>Requested Date</th>
                  <th>Account Number</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Admin Response</th>
                  <th>Reviewed Date</th>
                </tr>
              </thead>
              <tbody>
                {accountRequests.map((req) => {
                  const isReopenReq = req.requestType === "REOPEN";
                  return (
                    <tr key={req.requestId || req.id}>
                      <td>#{req.requestId || req.id}</td>
                      <td>
                        <span
                          className={`badge ${isReopenReq ? "badge-primary" : "badge-warning"}`}
                          style={{
                            display: "inline-block",
                            padding: "0.2rem 0.5rem",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            backgroundColor: isReopenReq
                              ? "var(--teal-100, #ccfbf1)"
                              : "var(--amber-100, #fef3c7)",
                            color: isReopenReq
                              ? "var(--teal-800, #115e59)"
                              : "var(--amber-800, #92400e)",
                          }}
                        >
                          {req.requestType || "CLOSURE"}
                        </span>
                      </td>
                      <td>{formatDateTime(req.requestedAt)}</td>
                      <td>{req.accountNumber}</td>
                      <td>
                        <div>{req.reason}</div>
                        {req.additionalNotes && (
                          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                            Note: {req.additionalNotes}
                          </div>
                        )}
                      </td>
                      <td>
                        <StatusBadge status={req.status} />
                      </td>
                      <td>{req.adminNotes || "—"}</td>
                      <td>{req.reviewedAt ? formatDateTime(req.reviewedAt) : "Pending Review"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
