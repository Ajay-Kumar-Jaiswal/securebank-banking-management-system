import { useEffect, useState } from "react";
import { getMyAccounts } from "../api/accountApi";
import { deposit } from "../api/transactionApi";
import { extractErrorMessage, formatCurrency } from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";
import ConfirmModal from "../components/ConfirmModal";

export default function Deposit() {
  const [accounts, setAccounts] = useState([]);
  const [accountId, setAccountId] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const res = await getMyAccounts();
      setAccounts(res.data);
      if (res.data.length > 0 && !accountId) {
        setAccountId(String(res.data[0].accountId));
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load accounts."));
    }
  };

  const selectedAccount = accounts.find((a) => String(a.accountId) === String(accountId));

  const handleOpenConfirm = (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const numAmount = Number(amount);
    if (!numAmount || numAmount <= 0) {
      setError("Please enter a valid deposit amount greater than zero.");
      return;
    }
    if (!selectedAccount) {
      setError("Please select an active account.");
      return;
    }
    if (selectedAccount.status !== "ACTIVE") {
      setError(`Cannot deposit into an account with status '${selectedAccount.status}'.`);
      return;
    }

    setShowConfirm(true);
  };

  const handleConfirmDeposit = async () => {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await deposit({
        accountId: Number(accountId),
        amount: Number(amount),
        description: description.trim() || undefined,
      });
      setSuccess(`Deposit successful! Reference: ${res.data.transactionReference}. New balance: ${formatCurrency(res.data.balanceAfter)}`);
      setAmount("");
      setDescription("");
      setShowConfirm(false);
      await loadAccounts();
    } catch (err) {
      setError(extractErrorMessage(err, "Deposit failed."));
      setShowConfirm(false);
    } finally {
      setSubmitting(false);
    }
  };

  const currentBal = selectedAccount ? Number(selectedAccount.balance) : 0;
  const depositNum = Number(amount) || 0;
  const projectedBal = currentBal + depositNum;

  return (
    <div className="page">
      <h1 className="page-title">Deposit Money</h1>
      <div className="card card-narrow">
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />
        <form onSubmit={handleOpenConfirm} className="auth-form">
          <label>
            Account
            <select
              value={accountId}
              onChange={(e) => setAccountId(e.target.value)}
              required
            >
              {accounts.map((acc) => (
                <option key={acc.accountId} value={acc.accountId}>
                  {acc.accountNumber} ({acc.accountType}) — {formatCurrency(acc.balance)} [{acc.status}]
                </option>
              ))}
            </select>
          </label>
          <label>
            Amount
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              required
            />
          </label>
          <label>
            Description (optional)
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g. Salary deposit, Cash deposit"
            />
          </label>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || !accountId || !amount || Number(amount) <= 0}
          >
            Review Deposit
          </button>
        </form>
      </div>

      <ConfirmModal
        isOpen={showConfirm}
        title="Confirm Deposit"
        confirmText="Confirm Deposit"
        confirmVariant="primary"
        loading={submitting}
        onCancel={() => setShowConfirm(false)}
        onConfirm={handleConfirmDeposit}
      >
        <div className="confirm-summary">
          <div className="confirm-summary-row">
            <span className="label">Target Account</span>
            <span className="value">{selectedAccount?.accountNumber} ({selectedAccount?.accountType})</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Current Balance</span>
            <span className="value">{formatCurrency(currentBal)}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Deposit Amount</span>
            <span className="value" style={{ color: "var(--teal-700)" }}>+ {formatCurrency(depositNum)}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Balance After Deposit</span>
            <span className="value">{formatCurrency(projectedBal)}</span>
          </div>
          {description && (
            <div className="confirm-summary-row">
              <span className="label">Description</span>
              <span className="value">{description}</span>
            </div>
          )}
        </div>
        <p className="modal-message">
          Please verify the deposit details above before confirming this transaction.
        </p>
      </ConfirmModal>
    </div>
  );
}
