"""
FastAPI application to sign into Microsoft 365 and send test emails.
Supports accounts with Two-Factor Authentication via OAuth2 device code flow.

Usage:
    1. Register an app in Azure Portal (see setup instructions below)
    2. Set environment variables in .env file
    3. Run: uvicorn email_test:app --reload
    4. Visit http://localhost:8000 and follow the authentication flow
"""

import os
import threading
import msal
import requests
from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Microsoft 365 Email Test", version="1.0.0")

# Configuration from environment variables
CLIENT_ID = os.getenv("MS_CLIENT_ID", "")
TENANT_ID = os.getenv("MS_TENANT_ID", "common")
SCOPES = ["Mail.Send", "User.Read"]

# Token and flow cache (in production, use a persistent cache)
app_state = {
    "access_token": None,
    "account": None,
    "pending_flow": None,
    "auth_status": "idle",  # idle, pending, success, error
    "auth_error": None,
}


class EmailReq(BaseModel):
    to_email: EmailStr
    subject: str = "Test Email from FastAPI"
    body: str = "This is a test email sent via Microsoft Graph API."


def get_msal_app():
    """Create MSAL public client application."""
    if not CLIENT_ID:
        raise ValueError("MS_CLIENT_ID environment variable not set")

    return msal.PublicClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
    )


def acquire_token_background(flow: dict):
    """Background task to wait for device code authentication."""
    try:
        msal_app = get_msal_app()
        result = msal_app.acquire_token_by_device_flow(flow)

        if "access_token" in result:
            app_state["access_token"] = result["access_token"]
            app_state["account"] = result.get("id_token_claims", {}).get("preferred_username", "Unknown")
            app_state["auth_status"] = "success"
        else:
            app_state["auth_status"] = "error"
            app_state["auth_error"] = result.get("error_description", result.get("error", "Unknown error"))
    except Exception as e:
        app_state["auth_status"] = "error"
        app_state["auth_error"] = str(e)
    finally:
        app_state["pending_flow"] = None


@app.get("/", response_class=HTMLResponse)
async def home():
    """Home page with status and links."""
    authenticated = app_state.get("access_token") is not None
    status = "Authenticated" if authenticated else "Not authenticated"
    account = app_state.get("account", "")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>M365 Email Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
            .status {{ padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
            .authenticated {{ background-color: #d4edda; color: #155724; }}
            .not-authenticated {{ background-color: #f8d7da; color: #721c24; }}
            a {{ display: inline-block; margin: 10px 10px 10px 0; padding: 10px 20px;
                 background-color: #0078d4; color: white; text-decoration: none; border-radius: 5px; }}
            a:hover {{ background-color: #005a9e; }}
            form {{ margin-top: 20px; }}
            label {{ font-weight: bold; }}
            input, textarea {{ width: 100%; padding: 10px; margin: 5px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
            button {{ background-color: #28a745; color: white; padding: 10px 20px; border: none;
                     border-radius: 5px; cursor: pointer; }}
            button:hover {{ background-color: #218838; }}
            pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            code {{ background: #e8e8e8; padding: 2px 6px; border-radius: 3px; }}
            .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <h1>Microsoft 365 Email Test</h1>
        <div class="status {'authenticated' if authenticated else 'not-authenticated'}">
            Status: {status}{f' ({account})' if account else ''}
        </div>

        <a href="/login">Login with Microsoft</a>
        <a href="/docs">API Documentation</a>
        {'<a href="/logout" style="background-color: #dc3545;">Logout</a>' if authenticated else ''}

        {'<h2>Send Test Email</h2><form action="/send-email-form" method="post">' +
         '<label>To:</label><input type="email" name="to_email" required placeholder="recipient@example.com">' +
         '<label>Subject:</label><input type="text" name="subject" value="Test Email from FastAPI">' +
         '<label>Body:</label><textarea name="body" rows="4">This is a test email sent via Microsoft Graph API.</textarea>' +
         '<button type="submit">Send Email</button></form>' if authenticated else ''}

        <h2>Setup Instructions</h2>

        <div class="warning">
            <strong>Important:</strong> The error "client is not supported for this feature" means you need to enable
            "Allow public client flows" in your Azure app registration (Step 6 below).
        </div>

        <ol>
            <li>Go to <a href="https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade" target="_blank">Azure Portal - App Registrations</a></li>
            <li>Click <strong>"New registration"</strong></li>
            <li>Name your app (e.g., "Email Test App")</li>
            <li>Select <strong>"Accounts in any organizational directory and personal Microsoft accounts"</strong></li>
            <li>Leave Redirect URI blank for now, click <strong>Register</strong></li>
            <li><strong>CRITICAL:</strong> Go to <strong>"Authentication"</strong> in the left menu:
                <ul>
                    <li>Scroll down to <strong>"Advanced settings"</strong></li>
                    <li>Set <strong>"Allow public client flows"</strong> to <strong>Yes</strong></li>
                    <li>Click <strong>Save</strong></li>
                </ul>
            </li>
            <li>Go to <strong>"API Permissions"</strong> in the left menu:
                <ul>
                    <li>Click "Add a permission"</li>
                    <li>Select "Microsoft Graph"</li>
                    <li>Select "Delegated permissions"</li>
                    <li>Search and add: <code>Mail.Send</code> and <code>User.Read</code></li>
                    <li>Click "Add permissions"</li>
                </ul>
            </li>
            <li>Go to <strong>"Overview"</strong> and copy the <strong>Application (client) ID</strong></li>
        </ol>

        <h3>.env file:</h3>
        <pre>MS_CLIENT_ID=your-application-client-id-here
MS_TENANT_ID=common</pre>

        <p><small>Note: Use <code>MS_TENANT_ID=common</code> for personal/work accounts, or your specific tenant ID for organization-only access.</small></p>
    </body>
    </html>
    """


@app.get("/login")
async def login():
    """Initiate device code flow for authentication (works with 2FA)."""
    try:
        msal_app = get_msal_app()
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Start device code flow
    flow = msal_app.initiate_device_flow(scopes=SCOPES)

    if "user_code" not in flow:
        error_desc = flow.get('error_description', 'Unknown error')

        # Provide helpful guidance for common errors
        if "not supported" in error_desc.lower() or "public client" in error_desc.lower():
            error_desc += (
                "\n\nTo fix this: Go to Azure Portal > App Registrations > Your App > "
                "Authentication > Advanced settings > Set 'Allow public client flows' to Yes"
            )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to create device flow: {error_desc}"
        )

    # Store the flow for the background token acquisition
    app_state["pending_flow"] = flow
    app_state["auth_status"] = "pending"
    app_state["auth_error"] = None

    # Start background thread to wait for authentication
    thread = threading.Thread(target=acquire_token_background, args=(flow,))
    thread.daemon = True
    thread.start()

    # Return instructions for the user
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - M365 Email Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
            .code {{ font-size: 32px; font-weight: bold; background: #f0f0f0; padding: 20px;
                    border-radius: 10px; margin: 20px 0; letter-spacing: 5px; user-select: all; }}
            a {{ color: #0078d4; }}
            a.button {{ display: inline-block; padding: 10px 20px; background-color: #0078d4;
                       color: white; text-decoration: none; border-radius: 5px; margin: 10px; }}
            .instructions {{ background: #e7f3ff; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: left; }}
            .status {{ margin-top: 30px; padding: 15px; border-radius: 5px; }}
            .pending {{ background: #fff3cd; color: #856404; }}
        </style>
        <script>
            // Poll for authentication status
            function checkStatus() {{
                fetch('/auth-status')
                    .then(r => r.json())
                    .then(data => {{
                        if (data.status === 'success') {{
                            window.location.href = '/?login=success';
                        }} else if (data.status === 'error') {{
                            document.getElementById('status').innerHTML =
                                '<div class="status" style="background:#f8d7da;color:#721c24;">Error: ' + data.error + '</div>';
                        }} else {{
                            setTimeout(checkStatus, 2000);
                        }}
                    }})
                    .catch(() => setTimeout(checkStatus, 2000));
            }}
            setTimeout(checkStatus, 3000);
        </script>
    </head>
    <body>
        <h1>Microsoft Login</h1>
        <div class="instructions">
            <p><strong>To sign in (including with 2FA):</strong></p>
            <ol>
                <li>Click the link below to open Microsoft login</li>
                <li>Enter the code shown below</li>
                <li>Complete sign-in (including any 2FA prompts)</li>
                <li>This page will automatically redirect when done</li>
            </ol>
        </div>

        <a href="{flow['verification_uri']}" target="_blank" class="button">Open Microsoft Login</a>

        <div class="code">{flow['user_code']}</div>

        <div id="status">
            <div class="status pending">
                Waiting for you to complete sign-in...
            </div>
        </div>

        <p><small>This code expires in {flow.get('expires_in', 900) // 60} minutes.</small></p>
        <p><a href="/">Cancel and go back</a></p>
    </body>
    </html>
    """)


@app.get("/auth-status")
async def auth_status():
    """Check authentication status (for polling)."""
    return {
        "status": app_state["auth_status"],
        "error": app_state.get("auth_error"),
        "account": app_state.get("account"),
    }


@app.post("/send-email")
async def send_email(email: EmailReq):
    """Send an email via Microsoft Graph API."""
    if not app_state.get("access_token"):
        raise HTTPException(status_code=401, detail="Not authenticated. Please login first.")

    # Prepare email message
    message = {
        "message": {
            "subject": email.subject,
            "body": {
                "contentType": "Text",
                "content": email.body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": email.to_email
                    }
                }
            ]
        },
        "saveToSentItems": "true"
    }

    # Send via Microsoft Graph
    response = requests.post(
        "https://graph.microsoft.com/v1.0/me/sendMail",
        headers={
            "Authorization": f"Bearer {app_state['access_token']}",
            "Content-Type": "application/json"
        },
        json=message
    )

    if response.status_code == 202:
        return {"status": "success", "message": f"Email sent to {email.to_email}"}
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Failed to send email: {response.text}"
        )


@app.post("/send-email-form")
async def send_email_form(
    to_email: str = Form(...),
    subject: str = Form("Test Email"),
    body: str = Form("Test")
):
    """Handle form submission for sending email."""
    try:
        await send_email(EmailReq(to_email=to_email, subject=subject, body=body))
        success = True
        error_msg = ""
    except HTTPException as e:
        success = False
        error_msg = e.detail

    if success:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Sent</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .success {{ background: #d4edda; color: #155724; padding: 20px; border-radius: 10px; }}
                a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #0078d4;
                     color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="success">
                <h1>Email Sent!</h1>
                <p>Successfully sent email to {to_email}</p>
            </div>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """)
    else:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Failed</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 10px; }}
                a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #0078d4;
                     color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h1>Failed to Send Email</h1>
                <p>{error_msg}</p>
            </div>
            <a href="/">Back to Home</a>
        </body>
        </html>
        """, status_code=400)


@app.get("/logout")
async def logout():
    """Clear the authentication token."""
    app_state["access_token"] = None
    app_state["account"] = None
    app_state["auth_status"] = "idle"
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logged Out</title>
        <meta http-equiv="refresh" content="2;url=/">
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; text-align: center; }
        </style>
    </head>
    <body>
        <h1>Logged Out</h1>
        <p>Redirecting to home...</p>
    </body>
    </html>
    """)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
