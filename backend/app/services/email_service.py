import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.models.email_log import EmailLog
from app.repositories.email_log_repository import EmailLogRepository


class EmailService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EmailLogRepository(db)

    def _send_email_raw(self, recipient: str, subject: str, text_body: str, html_body: Optional[str] = None) -> bool:
        """Sends an email via SMTP and writes to EmailLog. Never raises exceptions that crash callers."""
        status = "SENT"
        error_msg = None

        # Genuine Mock / Disabled Mode: ONLY if SMTP_HOST is genuinely missing or EMAILS_ENABLED is explicitly False
        if not settings.EMAILS_ENABLED or not (settings.SMTP_HOST and settings.SMTP_HOST.strip()):
            logger.info(f"SMTP not configured (EMAILS_ENABLED=False or SMTP_HOST missing). Mock sending email to {recipient}: '{subject}'")
            status = "SKIPPED"
        else:
            # REAL SMTP Sending Mode
            try:
                from_email = settings.SMTP_FROM_EMAIL.strip() if settings.SMTP_FROM_EMAIL else ""
                if not from_email:
                    from_email = settings.SMTP_USERNAME.strip() if settings.SMTP_USERNAME else "no-reply@securebank.com"

                from_name = settings.SMTP_FROM_NAME or "SecureBank Management System"

                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{from_name} <{from_email}>"
                msg["To"] = recipient

                part1 = MIMEText(text_body, "plain")
                msg.attach(part1)

                if html_body:
                    part2 = MIMEText(html_body, "html")
                    msg.attach(part2)

                logger.info(f"Connecting to SMTP server {settings.SMTP_HOST}:{settings.SMTP_PORT} to deliver email to {recipient}...")
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    if settings.SMTP_TLS:
                        server.starttls()
                    if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.sendmail(from_email, [recipient], msg.as_string())

                logger.info(f"Email successfully sent via SMTP to {recipient} with subject '{subject}'")
                status = "SENT"
            except Exception as e:
                status = "FAILED"
                raw_err = str(e)
                safe_err = raw_err
                if settings.SMTP_PASSWORD and settings.SMTP_PASSWORD in safe_err:
                    safe_err = safe_err.replace(settings.SMTP_PASSWORD, "******")
                error_msg = safe_err
                logger.error(f"SMTP email sending failed to {recipient}: {safe_err}")

        # Always log to EmailLog table
        try:
            log_entry = EmailLog(
                recipient_email=recipient,
                subject=subject,
                body=text_body,
                status=status,
                error_message=error_msg,
            )
            self.repo.create(log_entry)
            self.db.commit()
        except Exception as log_err:
            logger.error(f"Failed to save EmailLog: {log_err}")
            self.db.rollback()

        return status == "SENT"

    # --- Templated Emails ---

    def send_welcome_email(self, full_name: str, email: str) -> bool:
        subject = "Welcome to SecureBank"
        text = f"""Hello {full_name},

Welcome to SecureBank! Your profile has been created successfully.

Registered Email: {email}
Login Portal: {settings.FRONTEND_URL}/login

Security Reminder:
Never share your password, OTP, or account credentials with anyone. SecureBank will never ask for your password.

Thank you for choosing SecureBank.
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Welcome to SecureBank</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your profile has been created successfully.</p>
<p><strong>Registered Email:</strong> {email}</p>
<p><a href="{settings.FRONTEND_URL}/login" style="display: inline-block; padding: 10px 20px; background-color: #0f5c56; color: white; text-decoration: none; border-radius: 4px;">Log In to Your Account</a></p>
<hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
<p style="color: #666; font-size: 13px;">Security Reminder: Never share your password or security credentials with anyone. SecureBank will never contact you asking for your password.</p>
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_account_created_email(self, full_name: str, email: str, account_number: str, account_type: str, created_at: datetime) -> bool:
        subject = "Your Bank Account Has Been Created"
        created_str = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        text = f"""Hello {full_name},

Congratulations! Your new SecureBank account is ready.

Account Number: {account_number}
Account Type: {account_type}
Status: ACTIVE
Initial Balance: ₹0.00
Created At: {created_str}

You can now deposit funds or set up transfers via the portal: {settings.FRONTEND_URL}/dashboard
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Your New Account is Active</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your new bank account has been successfully created.</p>
<table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Account Number</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{account_number}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Account Type</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{account_type}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Initial Balance</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">₹0.00</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Status</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee; color: #146e66;">ACTIVE</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Date</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{created_str}</td></tr>
</table>
<p><a href="{settings.FRONTEND_URL}/dashboard" style="display: inline-block; padding: 10px 20px; background-color: #0f5c56; color: white; text-decoration: none; border-radius: 4px;">Go to Dashboard</a></p>
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_deposit_email(self, full_name: str, email: str, account_number: str, amount: Decimal, prev_balance: Decimal, new_balance: Decimal, reference: str, created_at: datetime) -> bool:
        subject = f"Deposit Confirmation - {reference}"
        date_str = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        text = f"""Hello {full_name},

Your deposit has been processed successfully.

Transaction Reference: {reference}
Account Number: {account_number}
Amount Deposited: ₹{amount:,.2f}
Previous Balance: ₹{prev_balance:,.2f}
New Balance: ₹{new_balance:,.2f}
Date/Time: {date_str}

Thank you for banking with SecureBank.
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Deposit Confirmation</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your deposit of <strong>₹{amount:,.2f}</strong> has been credited to your account.</p>
<table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Account Number</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{account_number}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Reference</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{reference}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Previous Balance</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">₹{prev_balance:,.2f}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>New Balance</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold; color: #146e66;">₹{new_balance:,.2f}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Date/Time</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{date_str}</td></tr>
</table>
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_withdrawal_email(self, full_name: str, email: str, account_number: str, amount: Decimal, prev_balance: Decimal, new_balance: Decimal, reference: str, created_at: datetime) -> bool:
        subject = f"Withdrawal Confirmation - {reference}"
        date_str = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        text = f"""Hello {full_name},

Your withdrawal has been completed successfully.

Transaction Reference: {reference}
Account Number: {account_number}
Amount Withdrawn: ₹{amount:,.2f}
Previous Balance: ₹{prev_balance:,.2f}
New Balance: ₹{new_balance:,.2f}
Date/Time: {date_str}

If you did not authorize this transaction, please contact bank support immediately.
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #8c2d2d;">Withdrawal Confirmation</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>A withdrawal of <strong>₹{amount:,.2f}</strong> has been debited from your account.</p>
<table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Account Number</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{account_number}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Reference</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{reference}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Previous Balance</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">₹{prev_balance:,.2f}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>New Balance</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">₹{new_balance:,.2f}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Date/Time</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{date_str}</td></tr>
</table>
<p style="color: #8c2d2d; font-size: 13px;">If you did not authorize this withdrawal, contact support immediately.</p>
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_transfer_sender_email(self, sender_name: str, sender_email: str, source_account: str, dest_account: str, amount: Decimal, prev_balance: Decimal, new_balance: Decimal, reference: str, created_at: datetime) -> bool:
        subject = f"Fund Transfer Sent - {reference}"
        date_str = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        text = f"""Hello {sender_name},

Your fund transfer of ₹{amount:,.2f} has been processed successfully.

Transaction Reference: {reference}
Source Account: {source_account}
Destination Account: {dest_account}
Amount: ₹{amount:,.2f}
Previous Balance: ₹{prev_balance:,.2f}
New Balance: ₹{new_balance:,.2f}
Date/Time: {date_str}
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Fund Transfer Sent</h2>
<p>Hello <strong>{sender_name}</strong>,</p>
<p>You have transferred <strong>₹{amount:,.2f}</strong> to account <strong>{dest_account}</strong>.</p>
<table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Reference</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{reference}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Source Account</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{source_account}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Destination Account</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{dest_account}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Amount</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">₹{amount:,.2f}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>New Balance</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee; font-weight: bold;">₹{new_balance:,.2f}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Date/Time</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{date_str}</td></tr>
</table>
</div>"""
        return self._send_email_raw(sender_email, subject, text, html)

    def send_transfer_receiver_email(self, receiver_name: str, receiver_email: str, dest_account: str, amount: Decimal, new_balance: Decimal, reference: str, created_at: datetime) -> bool:
        subject = f"Fund Transfer Received - {reference}"
        date_str = created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        text = f"""Hello {receiver_name},

You have received a fund transfer of ₹{amount:,.2f}.

Destination Account: {dest_account}
Amount Credited: ₹{amount:,.2f}
New Balance: ₹{new_balance:,.2f}
Transaction Reference: {reference}
Date/Time: {date_str}
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Funds Received</h2>
<p>Hello <strong>{receiver_name}</strong>,</p>
<p>You have received <strong>₹{amount:,.2f}</strong> into your account <strong>{dest_account}</strong>.</p>
<table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Reference</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{reference}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Account Number</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{dest_account}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Amount Credited</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee; color: #146e66; font-weight: bold;">₹{amount:,.2f}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>New Balance</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">₹{new_balance:,.2f}</td></tr>
<tr><td style="padding: 8px; border-bottom: 1px solid #eee;"><strong>Date/Time</strong></td><td style="padding: 8px; border-bottom: 1px solid #eee;">{date_str}</td></tr>
</table>
</div>"""
        return self._send_email_raw(receiver_email, subject, text, html)

    def send_closure_request_received_email(self, full_name: str, email: str, account_number: str) -> bool:
        subject = "Your account closure request has been received"
        text = f"""Hello {full_name},

Your request to close account {account_number} has been received and is currently under review by our operations team.

You can monitor the status of your request at: {settings.FRONTEND_URL}/account-closure
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Account Closure Request Received</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your request to close account <strong>{account_number}</strong> has been received and is pending administrative review.</p>
<p>We will notify you once a decision has been made.</p>
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_closure_approved_email(self, full_name: str, email: str, account_number: str, admin_notes: Optional[str] = None) -> bool:
        subject = "Your account closure request has been approved"
        notes_str = f"\nAdmin Notes: {admin_notes}\n" if admin_notes else ""
        text = f"""Hello {full_name},

Your account closure request for account {account_number} has been approved.
The account is now CLOSED and cannot be used for further transactions.{notes_str}
Your transaction history has been preserved securely according to banking regulations.
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Account Closure Approved</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your closure request for account <strong>{account_number}</strong> has been <strong>APPROVED</strong>.</p>
<p>The account status is now updated to CLOSED. All past transaction history remains archived and accessible for your records.</p>
{f"<p><strong>Admin Notes:</strong> {admin_notes}</p>" if admin_notes else ""}
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_closure_rejected_email(self, full_name: str, email: str, account_number: str, reason: str) -> bool:
        subject = "Your account closure request has been rejected"
        text = f"""Hello {full_name},

Your account closure request for account {account_number} has been rejected.

Reason / Notes: {reason}

Your account remains in its existing status. If you have questions, please reach out to customer support.
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #8c2d2d;">Account Closure Request Rejected</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your closure request for account <strong>{account_number}</strong> was <strong>REJECTED</strong>.</p>
<p><strong>Reason:</strong> {reason}</p>
<p>The account remains in its existing status.</p>
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_reopen_request_received_email(self, full_name: str, email: str, account_number: str) -> bool:
        subject = "Your account reopen request has been received"
        text = f"""Hello {full_name},

Your request to reopen account {account_number} has been received and is currently under review by our operations team.

You can monitor the status of your request at: {settings.FRONTEND_URL}/account-closure
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Account Reopen Request Received</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your request to reopen account <strong>{account_number}</strong> has been received and is pending administrative review.</p>
<p>We will notify you once a decision has been made.</p>
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_reopen_approved_email(self, full_name: str, email: str, account_number: str, admin_notes: Optional[str] = None) -> bool:
        subject = "Your account has been reopened"
        notes_str = f"\nAdmin Notes: {admin_notes}\n" if admin_notes else ""
        text = f"""Hello {full_name},

Your request to reopen account {account_number} has been approved.
The account is now ACTIVE and available for deposits, withdrawals, and transfers.{notes_str}
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #0f5c56;">Account Reopened Successfully</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your request to reopen account <strong>{account_number}</strong> has been <strong>APPROVED</strong>.</p>
<p>The account status is now updated to ACTIVE. You may resume all banking operations.</p>
{f"<p><strong>Admin Notes:</strong> {admin_notes}</p>" if admin_notes else ""}
</div>"""
        return self._send_email_raw(email, subject, text, html)

    def send_reopen_rejected_email(self, full_name: str, email: str, account_number: str, reason: str) -> bool:
        subject = "Your account reopen request has been rejected"
        text = f"""Hello {full_name},

Your request to reopen account {account_number} has been rejected.

Reason / Notes: {reason}

The account remains CLOSED. If you need assistance, please contact customer support.
"""
        html = f"""<div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px;">
<h2 style="color: #8c2d2d;">Account Reopen Request Rejected</h2>
<p>Hello <strong>{full_name}</strong>,</p>
<p>Your request to reopen account <strong>{account_number}</strong> was <strong>REJECTED</strong>.</p>
<p><strong>Reason:</strong> {reason}</p>
<p>The account remains CLOSED.</p>
</div>"""
        return self._send_email_raw(email, subject, text, html)

