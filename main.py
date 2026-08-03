import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DASHBOARD_USERNAME = "kmp"
DASHBOARD_PASSWORD = "Pakistan@2853"

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
        .login-container { background: white; border-radius: 15px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 50px; width: 100%; max-width: 400px; }
        .logo-section { text-align: center; margin-bottom: 30px; }
        .logo-section img { height: 60px; margin-bottom: 15px; }
        .logo-section h1 { color: #1e3a8a; font-size: 24px; margin-bottom: 5px; }
        .logo-section p { color: #0369a1; font-size: 13px; font-weight: 600; }
        .form-group { margin-bottom: 20px; }
        label { display: block; color: #333; font-weight: 600; margin-bottom: 8px; }
        input { width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 14px; }
        input:focus { outline: none; border-color: #1e3a8a; }
        button { width: 100%; padding: 12px; background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%); color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; }
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
        <form method="POST" action="/login">
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

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KMP Real Estate Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #1e3a8a 0%, #0369a1 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; border-radius: 15px; padding: 25px; margin-bottom: 25px; display: flex; justify-content: space-between; align-items: center; }
        .header-left { display: flex; gap: 20px; align-items: center; }
        .header-logo { height: 60px; }
        h1 { color: #1e3a8a; font-size: 28px; }
        p { color: #0369a1; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 25px; }
        .stat-card { background: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .stat-number { font-size: 32px; font-weight: bold; color: #1e3a8a; }
        .section { background: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; }
        .section h2 { color: #333; margin-bottom: 15px; }
        .logout { background: #ef4444; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; }
        .footer { text-align: center; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="header-left">
                <img src="https://raw.githubusercontent.com/gulraizmalik/reddit-lead-detector/main/KMP-LOGO.png" class="header-logo">
                <div>
                    <h1>KMP REAL ESTATE</h1>
                    <p>Lead Detection Dashboard</p>
                </div>
            </div>
            <a href="/logout" class="logout">Logout</a>
        </div>
        
        <div class="stats">
            <div class="stat-card"><h3>Total Leads</h3><div class="stat-number">0</div></div>
            <div class="stat-card"><h3>High Quality</h3><div class="stat-number">0</div></div>
            <div class="stat-card"><h3>Market Trend</h3><div class="stat-number">--</div></div>
            <div class="stat-card"><h3>Status</h3><div class="stat-number">✓</div></div>
        </div>
        
        <div class="section">
            <h2>📌 Latest Leads</h2>
            <p>Leads will appear here once Reddit monitoring activates...</p>
        </div>
        
        <div class="section">
            <h2>📊 Market Intelligence</h2>
            <p>Market data coming soon...</p>
        </div>
        
        <div class="footer">
            <p>🚀 KMP Real Estate AI Lead Detection System</p>
        </div>
    </div>
</body>
</html>
"""

@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard", status_code=302)

@app.post("/login")
async def login(request: Request):
    form = await request.form()
    username = form.get("username", "").strip()
    password = form.get("password", "").strip()
    
    if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(key="auth", value="ok", httponly=True, max_age=86400)
        return response
    
    return HTMLResponse(LOGIN_HTML + "<script>document.getElementById('error').style.display='block';</script>")

@app.get("/dashboard")
async def dashboard(request: Request):
    if request.cookies.get("auth") != "ok":
        return HTMLResponse(LOGIN_HTML)
    return HTMLResponse(DASHBOARD_HTML)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("auth")
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
