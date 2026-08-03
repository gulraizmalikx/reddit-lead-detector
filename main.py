import os
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="KMP Real Estate Lead Detection")

# Get credentials from environment
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "kmp")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "kmp123")

# Store active sessions
active_sessions = {}

# Login page HTML
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KMP Real Estate - Login</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 50px;
            width: 100%;
            max-width: 400px;
        }
        .logo-section {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo-section img {
            height: 60px;
            margin-bottom: 15px;
        }
        .logo-section h1 {
            color: #1e3a8a;
            font-size: 24px;
            margin-bottom: 5px;
        }
        .logo-section p {
            color: #0369a1;
            font-size: 13px;
            font-weight: 600;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            color: #333;
            font-weight: 600;
            margin-bottom: 8px;
            font-size: 14px;
        }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #1e3a8a;
            box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
        }
        .login-btn {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .login-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(30, 58, 138, 0.3);
        }
        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo-section">
            <img src="https://raw.githubusercontent.com/gulraizmalik/reddit-lead-detector/main/KMP-LOGO.png" alt="KMP Logo">
            <h1>KMP Real Estate</h1>
            <p>Lead Detection Dashboard</p>
        </div>
        
        <div class="error" id="error-msg">Invalid username or password</div>
        
        <form onsubmit="handleLogin(event)">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <button type="submit" class="login-btn">Login</button>
        </form>
    </div>

    <script>
        async function handleLogin(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            const response = await fetch('/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            if (response.ok) {
                window.location.href = '/dashboard';
            } else {
                document.getElementById('error-msg').style.display = 'block';
            }
        }
    </script>
</body>
</html>
"""

@app.get("/")
async def root():
    return {"message": "KMP Real Estate System - Visit /dashboard"}

@app.post("/login")
async def login(request: Request):
    data = await request.json()
    if data.get("username") == DASHBOARD_USERNAME and data.get("password") == DASHBOARD_PASSWORD:
        return {"status": "success"}
    return {"status": "failed"}, 401

@app.get("/login-page")
async def login_page():
    return HTMLResponse(LOGIN_HTML)

@app.get("/dashboard")
async def get_dashboard(request: Request):
    # Check if user is authenticated (simple check)
    auth = request.headers.get("Authorization", "")
    if auth != f"Bearer {DASHBOARD_PASSWORD}":
        # For simplicity, redirect to login page
        return HTMLResponse(LOGIN_HTML)
    return FileResponse("dashboard.html", media_type="text/html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "KMP Real Estate"}

@app.get("/api/reddit/leads")
async def get_leads():
    return {"leads": [], "total": 0}

@app.get("/api/trends/market-signal")
async def market_signal():
    return {"overall_trend": "stable", "top_cities": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
