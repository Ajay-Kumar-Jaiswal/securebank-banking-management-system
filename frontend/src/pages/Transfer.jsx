import { useEffect, useState } from "react";
import { getMyAccounts } from "../api/accountApi";
import { getBeneficiaries } from "../api/beneficiaryApi";
import { transfer } from "../api/transactionApi";
import { extractErrorMessage, formatCurrency } from "../utils/errorUtils";
import AlertMessage from "../components/AlertMessage";
import ConfirmModal from "../components/ConfirmModal";

export default function Transfer() {
  const [accounts, setAccounts] = useState([]);
  const [beneficiaries, setBeneficiaries] = useState([]);
  const [fromAccountId, setFromAccountId] = useState("");
  const [toAccountNumber, setToAccountNumber] = useState("");
  const [amount, setAmount] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [accRes, benRes] = await Promise.all([
        getMyAccounts(),
        getBeneficiaries(),
      ]);
      setAccounts(accRes.data);
      setBeneficiaries(benRes.data);
      if (accRes.data.length > 0 && !fromAccountId) {
        setFromAccountId(String(accRes.data[0].accountId));
      }
    } catch (err) {
      setError(extractErrorMessage(err, "Could not load transfer data."));
    }
  };

  const selectedSourceAccount = accounts.find((a) => String(a.accountId) === String(fromAccountId));

  const handleOpenConfirm = (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    const numAmount = Number(amount);
    if (!numAmount || numAmount <= 0) {
      setError("Please enter a valid transfer amount greater than zero.");
      return;
    }
    if (!selectedSourceAccount) {
      setError("Please select a valid source account.");
      return;
    }
    if (selectedSourceAccount.status !== "ACTIVE") {
      setError(`Cannot transfer from account with status '${selectedSourceAccount.status}'.`);
      return;
    }
    if (!toAccountNumber.trim()) {
      setError("Please specify the recipient account number.");
      return;
    }
    if (selectedSourceAccount.accountNumber === toAccountNumber.trim()) {
      setError("Source and destination accounts cannot be identical.");
      return;
    }
    if (Number(selectedSourceAccount.balance) < numAmount) {
      setError(`Insufficient funds. Your source balance is ${formatCurrency(selectedSourceAccount.balance)}.`);
      return;
    }

    setShowConfirm(true);
  };

  const handleConfirmTransfer = async () => {
    setSubmitting(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await transfer({
        fromAccountId: Number(fromAccountId),
        toAccountNumber: toAccountNumber.trim(),
        amount: Number(amount),
        description: description.trim() || undefined,
      });
      setSuccess(
        `Transfer successful! Reference: ${res.data.transactionReference}. Your new balance: ${formatCurrency(
          res.data.balanceAfter
        )}`
      );
      setAmount("");
      setDescription("");
      setToAccountNumber("");
      setShowConfirm(false);
      await loadData();
    } catch (err) {
      setError(extractErrorMessage(err, "Transfer failed."));
      setShowConfirm(false);
    } finally {
      setSubmitting(false);
    }
  };

  const currentBal = selectedSourceAccount ? Number(selectedSourceAccount.balance) : 0;
  const transferNum = Number(amount) || 0;
  const projectedBal = Math.max(0, currentBal - transferNum);

  return (
    <div className="page">
      <h1 className="page-title">Transfer Money</h1>
      <div className="card card-narrow">
        <AlertMessage message={error} />
        <AlertMessage type="success" message={success} />
        <form onSubmit={handleOpenConfirm} className="auth-form">
          <label>
            From Account
            <select
              value={fromAccountId}
              onChange={(e) => setFromAccountId(e.target.value)}
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
            To Account Number
            <input
              value={toAccountNumber}
              onChange={(e) => setToAccountNumber(e.target.value)}
              placeholder="e.g. AC-1002"
              required
            />
          </label>

          {beneficiaries.length > 0 && (
            <div className="beneficiary-quickpicks">
              <span>Quick pick saved payee:</span>
              {beneficiaries.map((b) => (
                <button
                  type="button"
                  key={b.beneficiaryId}
                  className="chip"
                  onClick={() => setToAccountNumber(b.accountNumber)}
                >
                  {b.name} ({b.accountNumber})
                </button>
              ))}
            </div>
          )}

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
              placeholder="e.g. Rent payment, Dinner split"
            />
          </label>

          <button
            type="submit"
            className="btn btn-primary"
            disabled={submitting || !fromAccountId || !toAccountNumber || !amount || Number(amount) <= 0}
          >
            Review Transfer
          </button>
        </form>
      </div>

      <ConfirmModal
        isOpen={showConfirm}
        title="Confirm Money Transfer"
        confirmText="Confirm Transfer"
        confirmVariant="primary"
        loading={submitting}
        onCancel={() => setShowConfirm(false)}
        onConfirm={handleConfirmTransfer}
      >
        <div className="confirm-summary">
          <div className="confirm-summary-row">
            <span className="label">Source Account</span>
            <span className="value">{selectedSourceAccount?.accountNumber} ({selectedSourceAccount?.accountType})</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Destination Account</span>
            <span className="value">{toAccountNumber}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Current Source Balance</span>
            <span className="value">{formatCurrency(currentBal)}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Transfer Amount</span>
            <span className="value" style={{ color: "var(--teal-700)" }}>{formatCurrency(transferNum)}</span>
          </div>
          <div className="confirm-summary-row">
            <span className="label">Balance After Transfer</span>
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
          Please confirm that you want to transfer this amount. Funds will be transferred immediately upon confirmation.
        </p>
      </ConfirmModal>
    </div>
  );
}
