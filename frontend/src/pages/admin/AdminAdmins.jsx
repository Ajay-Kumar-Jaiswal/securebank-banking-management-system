import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { getAllAdministrators, updateAdministratorStatus } from "../../api/adminApi";
import { extractErrorMessage, formatDateTime } from "../../utils/errorUtils";
import AlertMessage from "../../components/AlertMessage";
import StatusBadge from "../../components/StatusBadge";
import ConfirmModal from "../../components/ConfirmModal";

export default function AdminAdmins() {
  const { user: currentAdmin } = useAuth();
  const [admins, setAdmins] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [loading, setLoading] = useState(true);

  // Status Modal state
  const [statusModal, setStatusModal] = useState({
    isOpen: false,
    admin: null,
    newStatus: "",
  });
  const [updating, setUpdating] = useState(false);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getAllAdministrators();
      setAdmins(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load administrator accounts."));
    } finally {
      setLoading(false);
    }
  };

  const promptStatusChange = (admin, newStatus) => {
    setError(null);
    setSuccess(null);

    // Front-end check for self-deactivation
    if (admin.userId === currentAdmin?.userId && newStatus !== "ACTIVE") {
      setError("You cannot deactivate your own administrator account.");
      return;
    }

    setStatusModal({
      isOpen: true,
      admin,
      newStatus,
    });
  };

  const handleConfirmStatusChange = async () => {
    if (!statusModal.admin || !statusModal.newStatus) return;

    setUpdating(true);
    setError(null);
    setSuccess(null);

    const targetAdmin = statusModal.admin;
    const nextStatus = statusModal.newStatus;

    try {
      await updateAdministratorStatus(targetAdmin.userId, nextStatus);
      const actionName = nextStatus === "ACTIVE" ? "activated" : "deactivated";
      setSuccess(`Administrator ${targetAdmin.fullName} (${targetAdmin.email}) has been successfully ${actionName}.`);
      setStatusModal({ isOpen: false, admin: null, newStatus: "" });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, `Failed to update administrator status.`));
      setStatusModal({ isOpen: false, admin: null, newStatus: "" });
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="page">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h1 className="page-title" style={{ margin: 0 }}>Administrator Management</h1>
        <button className="btn btn-sm btn-secondary" onClick={load}>
          Refresh
        </button>
      </div>

      <div className="card">
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />

        <div style={{ marginBottom: "1rem", color: "var(--text-muted)", fontSize: "0.92rem" }}>
          Manage administrative privileges and access controls. The system enforces strict lockout safeguards, requiring at least one active administrator at all times.
        </div>

        {loading ? (
          <p>Loading administrators...</p>
        ) : admins.length === 0 ? (
          <p>No administrators found.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {admins.map((adm) => {
                  const isSelf = currentAdmin && adm.userId === currentAdmin.userId;
                  return (
                    <tr key={adm.userId}>
                      <td>#{adm.userId}</td>
                      <td>
                        <strong>{adm.fullName}</strong>
                        {isSelf && (
                          <span style={{ marginLeft: "0.5rem", fontSize: "0.75rem", color: "var(--teal-700)", fontWeight: 600 }}>
                            (You)
                          </span>
                        )}
                      </td>
                      <td>{adm.email}</td>
                      <td>
                        <span className="role-tag" style={{ marginLeft: 0 }}>{adm.role}</span>
                      </td>
                      <td>
                        <StatusBadge status={adm.status} />
                      </td>
                      <td>{formatDateTime(adm.createdAt)}</td>
                      <td className="action-cell">
                        {isSelf ? (
                          <button
                            className="btn btn-sm btn-secondary"
                            disabled
                            title="You cannot deactivate your own administrator account."
                            style={{ opacity: 0.6, cursor: "not-allowed" }}
                          >
                            Protected (Self)
                          </button>
                        ) : adm.status === "ACTIVE" ? (
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => promptStatusChange(adm, "DEACTIVATED")}
                          >
                            Deactivate
                          </button>
                        ) : (
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => promptStatusChange(adm, "ACTIVE")}
                          >
                            Activate
                          </button>
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

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={statusModal.isOpen}
        title={statusModal.newStatus === "DEACTIVATED" ? "Deactivate Administrator?" : "Activate Administrator?"}
        confirmText={statusModal.newStatus === "DEACTIVATED" ? "Deactivate" : "Activate"}
        confirmVariant={statusModal.newStatus === "DEACTIVATED" ? "danger" : "primary"}
        loading={updating}
        onCancel={() => setStatusModal({ isOpen: false, admin: null, newStatus: "" })}
        onConfirm={handleConfirmStatusChange}
      >
        <div className="confirm-summary">
          <div className="confirm-summary-row">
            <span className="label">Name</span>
            <span className="value">{statusModal.admin?.fullName}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Email</span>
            <span className="value">{statusModal.admin?.email}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Role</span>
            <span className="value">{statusModal.admin?.role}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Target Status</span>
            <span className="value">{statusModal.newStatus}</span>
          </div>
        </div>

        <p className="modal-message">
          {statusModal.newStatus === "DEACTIVATED"
            ? "This administrator will no longer be able to log in."
            : "This administrator will regain full access to the Admin Portal."}
        </p>

        {statusModal.newStatus === "DEACTIVATED" && (
          <div className="warning-callout">
            <strong>Important:</strong> Deactivating an administrator revokes their access immediately. You cannot deactivate the last active administrator.
          </div>
        )}
      </ConfirmModal>
    </div>
  );
}
