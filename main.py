import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse

app = FastAPI(title="KMP Real Estate Lead Detection")

# Credentials
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "kmp")
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "kmp123")

LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KMP Real Estate - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
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
        .logo-section { text-align: center; margin-bottom: 30px; }
        .logo-section img { height: 60px; margin-bottom: 15px; }
        .logo-section h1 { color: #1e3a8a; font-size: 24px; margin-bottom: 5px; }
        .logo-section p { color: #0369a1; font-size: 13px; font-weight: 600; }
        .form-group { margin-bottom: 20px; }
        label { display: block; color: #333; font-weight: 600; margin-bottom: 8px; }
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
        }
        input:focus { outline: none; border-color: #1e3a8a; }
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
        }
        button:hover { transform: translateY(-2px); }
        .error { background: #fee2e2; color: #991b1b; padding: 12px; border-radius: 8px; margin-bottom: 20px; display: none; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo-section">
            <img src="https://raw.githubusercontent.com/gulraizmalik/reddit-lead-detector/main/KMP-LOGO.png" alt="KMP">
            <h1>KMP Real Estate</h1>
            <p>Lead Detection Dashboard</p>
        </div>
        <div class="error" id="error">Invalid credentials</div>
        <form method="POST" action="/api/login">
            <div class="form-group">
                <label>Username</label>
                <input type="text" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>
"""

@app.get("/")
async def root():
    return {"message": "KMP Real Estate - Visit /dashboard"}

@app.get("/api/login-page")
async def login_page():
    return HTMLResponse(LOGIN_HTML)

@app.post("/api/login")
async def login(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    
    if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="auth_token", value="authenticated", httponly=True)
        return response
    
    return HTMLResponse(LOGIN_HTML + "<script>document.getElementById('error').style.display='block';</script>")

@app.get("/dashboard")
async def get_dashboard(request: Request):
    auth = request.cookies.get("auth_token")
    if auth != "authenticated":
        return RedirectResponse(url="/api/login-page", status_code=302)
    return FileResponse("dashboard.html", media_type="text/html")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/reddit/leads")
async def get_leads():
    return {"leads": [], "total": 0}

@app.get("/api/trends/market-signal")
async def market_signal():
    return {"overall_trend": "stable", "top_cities": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
