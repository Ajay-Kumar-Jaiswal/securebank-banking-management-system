import { useEffect, useState } from "react";
import { getMyAccounts } from "../api/accountApi";
import { withdraw } from "../api/transactionApi";
import { extractErrorMessage, formatCurrency } from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";
import ConfirmModal from "../components/ConfirmModal";

export default function Withdraw() {
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
      setError("Please enter a valid withdrawal amount greater than zero.");
      return;
    }
    if (!selectedAccount) {
      setError("Please select an active account.");
      return;
    }
    if (selectedAccount.status !== "ACTIVE") {
      setError(`Cannot withdraw from an account with status '${selectedAccount.status}'.`);
      return;
    }
    if (Number(selectedAccount.balance) < numAmount) {
      setError(`Insufficient funds. Your available balance is ${formatCurrency(selectedAccount.balance)}.`);
      return;
    }

    setShowConfirm(true);
  };

  const handleConfirmWithdraw = async () => {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await withdraw({
        accountId: Number(accountId),
        amount: Number(amount),
        description: description.trim() || undefined,
      });
      setSuccess(`Withdrawal successful! Reference: ${res.data.transactionReference}. Remaining balance: ${formatCurrency(res.data.balanceAfter)}`);
      setAmount("");
      setDescription("");
      setShowConfirm(false);
      await loadAccounts();
    } catch (err) {
      setError(extractErrorMessage(err, "Withdrawal failed."));
      setShowConfirm(false);
    } finally {
      setSubmitting(false);
    }
  };

  const currentBal = selectedAccount ? Number(selectedAccount.balance) : 0;
  const withdrawNum = Number(amount) || 0;
  const projectedBal = Math.max(0, currentBal - withdrawNum);

  return (
    <div className="page">
      <h1 className="page-title">Withdraw Money</h1>
      <div className="card card-narrow">
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />
        <form onSubmit={handleOpenConfirm} className="auth-form">
          <label>
            Source Account
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
              placeholder="e.g. ATM withdrawal, Personal expenses"
            />
          </label>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || !accountId || !amount || Number(amount) <= 0}
          >
            Review Withdrawal
          </button>
        </form>
      </div>

      <ConfirmModal
        isOpen={showConfirm}
        title="Confirm Withdrawal"
        confirmText="Confirm Withdrawal"
        confirmVariant="danger"
        loading={submitting}
        onCancel={() => setShowConfirm(false)}
        onConfirm={handleConfirmWithdraw}
      >
        <div className="confirm-summary">
          <div className="confirm-summary-row">
            <span className="label">Source Account</span>
            <span className="value">{selectedAccount?.accountNumber} ({selectedAccount?.accountType})</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Current Balance</span>
            <span className="value">{formatCurrency(currentBal)}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Withdrawal Amount</span>
            <span className="value" style={{ color: "var(--red-700)" }}>- {formatCurrency(withdrawNum)}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Balance After Withdrawal</span>
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
          Please verify that you wish to withdraw these funds from your account.
        </p>
      </ConfirmModal>
    </div>
  );
}
