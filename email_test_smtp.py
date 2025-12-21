"""
FastAPI application that sends login codes via SMTP email.
Works with any SMTP server (Gmail, Outlook, custom SMTP, etc.)

Usage:
    1. Set environment variables in .env file
    2. Run: uvicorn email_test_smtp:app --reload
    3. POST to /request-code with an email address
"""

import os
import random
import string
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Email Login Code Service (SMTP)", version="1.0.0")

# SMTP Configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # App password if 2FA enabled
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "") or SMTP_USERNAME
SENDER_NAME = os.getenv("SENDER_NAME", "Login Service")

# Allowed emails (in production, use a database)
ALLOWED_EMAILS = set(
    email.strip().lower()
    for email in os.getenv("ALLOWED_EMAILS", "").split(",")
    if email.strip()
)

# Code storage (in production, use Redis or a database with TTL)
pending_codes: dict[str, dict] = {}


class CodeRequest(BaseModel):
    email: EmailStr


class CodeVerify(BaseModel):
    email: EmailStr
    code: str


def generate_code(length: int = 6) -> str:
    """Generate a random numeric code."""
    return "".join(random.choices(string.digits, k=length))


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email using SMTP."""
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD]):
        raise ValueError("SMTP not configured. Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD")

    # Create message
    msg = MIMEMultipart()
    msg["From"] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        print("Sending ...")
        cont = ssl.create_default_context()
        server = smtplib.SMTP(SMTP_HOST, port=SMTP_PORT)
        server.starttls(context = cont)
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()
        print("Done")
        # if SMTP_USE_TLS:
        #     # STARTTLS (port 587)
        #     server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        #     server.starttls()
        # else:
        #     # SSL (port 465) or plain (port 25)
        #     if SMTP_PORT == 465:
        #         server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT)
        #     else:
        #         server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)

        # server.login(SMTP_USERNAME, SMTP_PASSWORD)
        # print("A")
        # server.send_message(msg)
        # print("B")
        # server.quit()
        # print("C")

        return True

    except smtplib.SMTPAuthenticationError as e:
        raise HTTPException(
            status_code=500,
            detail=f"SMTP authentication failed. If using 2FA, use an App Password. Error: {e}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {e}")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with login form."""
    configured = all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD])
    has_allowed = len(ALLOWED_EMAILS) > 0

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login with Email Code (SMTP)</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .form-group {{ margin-bottom: 20px; }}
            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
            input {{ width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
            button {{ background-color: #0078d4; color: white; padding: 12px 24px; border: none;
                     border-radius: 4px; cursor: pointer; font-size: 16px; }}
            button:hover {{ background-color: #005a9e; }}
            .status {{ padding: 10px; border-radius: 4px; margin-bottom: 20px; }}
            .ok {{ background-color: #d4edda; color: #155724; }}
            .error {{ background-color: #f8d7da; color: #721c24; }}
            pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 12px; }}
            code {{ background: #e8e8e8; padding: 2px 6px; border-radius: 3px; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background: #f4f4f4; }}
        </style>
    </head>
    <body>
        <h1>Login with Email Code</h1>
        <p><em>SMTP Version</em></p>

        <div class="status {'ok' if configured else 'error'}">
            {'Configuration: OK' if configured else 'Configuration: Missing SMTP settings'}
        </div>

        {'<div class="status error">No allowed emails configured. Set ALLOWED_EMAILS in .env</div>' if not has_allowed else ''}

        <h2>Step 1: Request Code</h2>
        <form action="/request-code-form" method="post">
            <div class="form-group">
                <label>Email Address:</label>
                <input type="email" name="email" required placeholder="your@email.com">
            </div>
            <button type="submit">Send Login Code</button>
        </form>

        <h2>Step 2: Verify Code</h2>
        <form action="/verify-code-form" method="post">
            <div class="form-group">
                <label>Email Address:</label>
                <input type="email" name="email" required placeholder="your@email.com">
            </div>
            <div class="form-group">
                <label>6-Digit Code:</label>
                <input type="text" name="code" required placeholder="123456" pattern="[0-9]{{6}}" maxlength="6">
            </div>
            <button type="submit">Verify Code</button>
        </form>

        <hr style="margin: 40px 0;">

        <h2>SMTP Settings</h2>

        <h3>Common SMTP Servers:</h3>
        <table>
            <tr><th>Provider</th><th>Host</th><th>Port</th><th>TLS</th></tr>
            <tr><td>Microsoft 365 / Outlook</td><td>smtp.office365.com</td><td>587</td><td>Yes</td></tr>
            <tr><td>Gmail</td><td>smtp.gmail.com</td><td>587</td><td>Yes</td></tr>
            <tr><td>Yahoo</td><td>smtp.mail.yahoo.com</td><td>587</td><td>Yes</td></tr>
            <tr><td>iCloud</td><td>smtp.mail.me.com</td><td>587</td><td>Yes</td></tr>
        </table>

        <h3>.env file:</h3>
        <pre># SMTP Settings
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yourcompany.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true

# Optional: if sender differs from username
SENDER_EMAIL=noreply@yourcompany.com
SENDER_NAME=My App

# Allowed users
ALLOWED_EMAILS=user1@example.com,user2@example.com</pre>

        <h3>Important: App Passwords</h3>
        <p>If your account has <strong>Two-Factor Authentication (2FA)</strong> enabled, you must use an <strong>App Password</strong> instead of your regular password:</p>
        <ul>
            <li><strong>Microsoft 365:</strong> <a href="https://account.microsoft.com/security" target="_blank">Security settings</a> → App passwords</li>
            <li><strong>Gmail:</strong> <a href="https://myaccount.google.com/apppasswords" target="_blank">App passwords</a> (requires 2FA enabled)</li>
        </ul>
    </body>
    </html>
    """


@app.post("/request-code")
async def request_code(request: CodeRequest):
    """Request a login code to be sent to an email address."""
    email = request.email.lower()

    # Check if email is allowed
    if email not in ALLOWED_EMAILS:
        # Don't reveal whether email exists
        return {"status": "success", "message": "If this email is registered, a code has been sent."}

    # Generate code
    code = generate_code()
    expires_at = datetime.now() + timedelta(minutes=10)

    # Store code
    pending_codes[email] = {
        "code": code,
        "expires_at": expires_at,
        "attempts": 0,
    }

    # Send email
    try:
        send_email(
            to_email=email,
            subject="Your Login Code",
            body=f"Your login code is: {code}\n\nThis code expires in 10 minutes.",
        )
    except Exception as e:
        # Log error but don't reveal to user
        print(f"Failed to send email to {email}: {e}")

    return {"status": "success", "message": "If this email is registered, a code has been sent."}


@app.post("/verify-code")
async def verify_code(request: CodeVerify):
    """Verify a login code."""
    email = request.email.lower()
    code = request.code.strip()

    # Check if there's a pending code for this email
    if email not in pending_codes:
        raise HTTPException(status_code=401, detail="Invalid or expired code")

    stored = pending_codes[email]

    # Check expiry
    if datetime.now() > stored["expires_at"]:
        del pending_codes[email]
        raise HTTPException(status_code=401, detail="Code has expired")

    # Check attempts (prevent brute force)
    if stored["attempts"] >= 5:
        del pending_codes[email]
        raise HTTPException(status_code=401, detail="Too many attempts. Request a new code.")

    # Verify code
    if code != stored["code"]:
        stored["attempts"] += 1
        raise HTTPException(status_code=401, detail="Invalid code")

    # Success - clear the code
    del pending_codes[email]

    # In a real app, you would create a session/JWT here
    return {
        "status": "success",
        "message": "Login successful",
        "email": email,
    }


@app.post("/request-code-form")
async def request_code_form(email: str = Form(...)):
    """Handle form submission for requesting a code."""
    result = await request_code(CodeRequest(email=email))
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Code Sent</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
            .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; }}
            a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #0078d4;
                 color: white; text-decoration: none; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="success">
            <h1>Check Your Email</h1>
            <p>{result['message']}</p>
        </div>
        <a href="/">Back to Login</a>
    </body>
    </html>
    """)


@app.post("/verify-code-form")
async def verify_code_form(email: str = Form(...), code: str = Form(...)):
    """Handle form submission for verifying a code."""
    try:
        result = await verify_code(CodeVerify(email=email, code=code))
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Successful</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; }}
            </style>
        </head>
        <body>
            <div class="success">
                <h1>Login Successful!</h1>
                <p>Welcome, {result['email']}</p>
            </div>
        </body>
        </html>
        """)
    except HTTPException as e:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Login Failed</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; }}
                a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #0078d4;
                     color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>Login Failed</h1>
                <p>{e.detail}</p>
            </div>
            <a href="/">Try Again</a>
        </body>
        </html>
        """, status_code=401)


@app.get("/test-smtp")
async def test_smtp():
    """Test SMTP connection (for debugging)."""
    if not all([SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD]):
        return {"status": "error", "message": "SMTP not configured"}

    try:
        if SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.starttls()
        else:
            if SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
            else:
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)

        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.quit()
        return {"status": "success", "message": "SMTP connection successful"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
