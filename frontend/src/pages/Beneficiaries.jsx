import { useEffect, useState } from "react";
import { getBeneficiaries, addBeneficiary, deleteBeneficiary } from "../api/beneficiaryApi";
import { extractErrorMessage } from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";
import ConfirmModal from "../components/ConfirmModal";

const initialForm = { name: "", accountNumber: "", bankName: "", ifscCode: "" };

export default function Beneficiaries() {
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Delete modal state
  const [deleteModal, setDeleteModal] = useState({ isOpen: false, beneficiary: null });
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    try {
      const res = await getBeneficiaries();
      setBeneficiaries(res.data);
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load beneficiaries."));
    }
  };

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleAdd = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSubmitting(true);
    try {
      await addBeneficiary(form);
      setSuccess("Beneficiary added successfully.");
      setForm(initialForm);
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not add beneficiary. Please verify destination account number."));
    } finally {
      setSubmitting(false);
    }
  };

  const promptDelete = (b) => {
    setDeleteModal({ isOpen: true, beneficiary: b });
  };

  const handleConfirmDelete = async () => {
    if (!deleteModal.beneficiary) return;
    setDeleting(true);
    setError(null);
    try {
      await deleteBeneficiary(deleteModal.beneficiary.beneficiaryId);
      setSuccess(`Beneficiary ${deleteModal.beneficiary.name} removed.`);
      setDeleteModal({ isOpen: false, beneficiary: null });
      await load();
    } catch (err) {
      setError(extractErrorMessage(err, "Could not delete beneficiary."));
      setDeleteModal({ isOpen: false, beneficiary: null });
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="page">
      <h1 className="page-title">Beneficiaries</h1>

      <div className="card">
        <h2>Add a Beneficiary</h2>
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />
        <form onSubmit={handleAdd} className="auth-form">
          <label>
            Beneficiary Name
            <input
              name="name"
              placeholder="e.g. John Doe"
              value={form.name}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Destination Account Number
            <input
              name="accountNumber"
              placeholder="e.g. AC4393409220"
              value={form.accountNumber}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            Bank Name
            <input
              name="bankName"
              placeholder="e.g. SecureBank"
              value={form.bankName}
              onChange={handleChange}
              required
            />
          </label>
          <label>
            IFSC / Routing Code
            <input
              name="ifscCode"
              placeholder="e.g. SECB0001234"
              value={form.ifscCode}
              onChange={handleChange}
              required
            />
          </label>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Verifying & Adding..." : "Add Beneficiary"}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>Saved Beneficiaries</h2>
        {beneficiaries.length === 0 ? (
          <p>You haven't added any beneficiaries yet.</p>
        ) : (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Account Number</th>
                  <th>Bank</th>
                  <th>IFSC</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {beneficiaries.map((b) => (
                  <tr key={b.beneficiaryId}>
                    <td><strong>{b.name}</strong></td>
                    <td>{b.accountNumber}</td>
                    <td>{b.bankName}</td>
                    <td>{b.ifscCode}</td>
                    <td>
                      <button
                        className="btn btn-danger btn-sm"
                        onClick={() => promptDelete(b)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ConfirmModal
        isOpen={deleteModal.isOpen}
        title="Remove Beneficiary"
        confirmText="Remove Beneficiary"
        confirmVariant="danger"
        loading={deleting}
        onCancel={() => setDeleteModal({ isOpen: false, beneficiary: null })}
        onConfirm={handleConfirmDelete}
      >
        <p className="modal-message">
          Are you sure you want to remove <strong>{deleteModal.beneficiary?.name}</strong> ({deleteModal.beneficiary?.accountNumber}) from your saved beneficiaries?
        </p>
      </ConfirmModal>
    </div>
  );
}
