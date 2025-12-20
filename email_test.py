"""
FastAPI application that sends login codes via Microsoft 365 email.
Uses application-level authentication (client credentials flow) so the app
can send emails without user interaction.

Usage:
    1. Register an app in Azure Portal with application permissions
    2. Set environment variables in .env file
    3. Run: uvicorn email_test:app --reload
    4. POST to /request-code with an email address
"""

import os
import random
import string
from datetime import datetime, timedelta

import msal
import requests
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Email Login Code Service", version="1.0.0")

# Configuration from environment variables
CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET", "")
TENANT_ID = os.getenv("MS_TENANT_ID", "")  # Required for app-only auth
SENDER_EMAIL = os.getenv("MS_SENDER_EMAIL", "")  # The mailbox to send from

# Allowed emails (in production, use a database)
ALLOWED_EMAILS = set(
    email.strip().lower()
    for email in os.getenv("ALLOWED_EMAILS", "").split(",")
    if email.strip()
)

# Code storage (in production, use Redis or a database with TTL)
pending_codes: dict[str, dict] = {}

# Token cache
app_token_cache = {"access_token": None, "expires_at": None}


class CodeRequest(BaseModel):
    email: EmailStr


class CodeVerify(BaseModel):
    email: EmailStr
    code: str


def get_app_token() -> str:
    """Get an application access token using client credentials flow."""
    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        raise ValueError(
            "Missing configuration. Set MS_CLIENT_ID, MS_CLIENT_SECRET, and MS_TENANT_ID"
        )

    # Check cached token
    if (
        app_token_cache["access_token"]
        and app_token_cache["expires_at"]
        and datetime.now() < app_token_cache["expires_at"]
    ):
        return app_token_cache["access_token"]

    # Get new token
    msal_app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )

    result = msal_app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )

    if "access_token" not in result:
        error = result.get("error_description", result.get("error", "Unknown error"))
        raise ValueError(f"Failed to get token: {error}")

    app_token_cache["access_token"] = result["access_token"]
    app_token_cache["expires_at"] = datetime.now() + timedelta(
        seconds=result.get("expires_in", 3600) - 60
    )

    return result["access_token"]


def generate_code(length: int = 6) -> str:
    """Generate a random numeric code."""
    return "".join(random.choices(string.digits, k=length))


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send an email using Microsoft Graph API."""
    if not SENDER_EMAIL:
        raise ValueError("MS_SENDER_EMAIL not configured")

    token = get_app_token()

    message = {
        "message": {
            "subject": subject,
            "body": {"contentType": "Text", "content": body},
            "toRecipients": [{"emailAddress": {"address": to_email}}],
        },
        "saveToSentItems": "false",
    }

    # Use the specific user's sendMail endpoint
    response = requests.post(
        f"https://graph.microsoft.com/v1.0/users/{SENDER_EMAIL}/sendMail",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json=message,
    )

    if response.status_code == 202:
        return True
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send email: {response.status_code} - {response.text}",
        )


@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with login form."""
    configured = all([CLIENT_ID, CLIENT_SECRET, TENANT_ID, SENDER_EMAIL])
    has_allowed = len(ALLOWED_EMAILS) > 0

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login with Email Code</title>
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
        </style>
    </head>
    <body>
        <h1>Login with Email Code</h1>

        <div class="status {'ok' if configured else 'error'}">
            {'Configuration: OK' if configured else 'Configuration: Missing environment variables'}
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

        <h2>Setup Instructions</h2>
        <ol>
            <li>Go to <a href="https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade" target="_blank">Azure Portal - App Registrations</a></li>
            <li>Create a new registration (or use existing)</li>
            <li>Go to <strong>"Certificates &amp; secrets"</strong> → Create a new client secret → Copy the value</li>
            <li>Go to <strong>"API Permissions"</strong>:
                <ul>
                    <li>Click "Add a permission"</li>
                    <li>Select "Microsoft Graph"</li>
                    <li>Select <strong>"Application permissions"</strong> (not Delegated!)</li>
                    <li>Search and add: <code>Mail.Send</code></li>
                    <li>Click "Grant admin consent" (requires admin)</li>
                </ul>
            </li>
            <li>Note your Tenant ID from "Overview"</li>
        </ol>

        <h3>.env file:</h3>
        <pre>MS_CLIENT_ID=your-application-client-id
MS_CLIENT_SECRET=your-client-secret-value
MS_TENANT_ID=your-tenant-id
MS_SENDER_EMAIL=noreply@yourcompany.com
ALLOWED_EMAILS=user1@example.com,user2@example.com</pre>

        <p><small>Note: The sender email must be a valid mailbox in your Microsoft 365 tenant.</small></p>
    </body>
    </html>
    """


@app.post("/request-code")
async def request_code(request: CodeRequest):
    """Request a login code to be sent to an email address."""
    email = request.email.lower()

    # Check if email is allowed
    if email not in ALLOWED_EMAILS:
        # Don't reveal whether email exists - just say code sent
        # (In production, you might want to rate limit this)
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
