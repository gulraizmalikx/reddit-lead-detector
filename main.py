import os
import json
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import praw
from anthropic import Anthropic

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/reddit_leads")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Credentials
DASHBOARD_USERNAME = "kmp"
DASHBOARD_PASSWORD = "Pakistan@2853"
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.getenv("REDDIT_PASSWORD", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

app = FastAPI()

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KMP Real Estate - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 400px;
        }
        .logo { text-align: center; margin-bottom: 30px; }
        .logo h1 { color: #333; font-size: 28px; margin-bottom: 5px; }
        .logo p { color: #666; font-size: 14px; }
        .form-group {
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
        }
        label {
            font-size: 14px;
            color: #333;
            margin-bottom: 8px;
            font-weight: 600;
        }
        input {
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 5px rgba(102, 126, 234, 0.3);
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            border: none;
            border-radius: 5px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
        }
        button:hover { transform: translateY(-2px); }
        .error { color: #dc3545; font-size: 14px; text-align: center; display: none; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo">
            <h1>🏢 KMP REAL ESTATE</h1>
            <p>Lead Detection Dashboard</p>
        </div>
        <form method="post" action="/auth">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" name="username" required autofocus>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit">Login</button>
            <div class="error" id="error">Invalid credentials</div>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KMP Real Estate Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        header {
            background: white;
            padding: 20px 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        header h1 {
            font-size: 28px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        header img {
            height: 40px;
            width: auto;
        }
        .logout-btn {
            background: #dc3545;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
        }
        .logout-btn:hover { background: #c82333; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
            font-weight: 600;
        }
        .stat-card .value {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }
        .filters {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .filter-btn {
            padding: 10px 20px;
            border: 2px solid #ddd;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .filter-btn:hover { border-color: #667eea; color: #667eea; }
        .filter-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        .section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .section h2 {
            font-size: 20px;
            margin-bottom: 20px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .leads-list {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .lead-card {
            border: 1px solid #eee;
            padding: 15px;
            border-radius: 5px;
            background: #f9f9f9;
        }
        .lead-card h4 {
            color: #333;
            margin-bottom: 5px;
        }
        .lead-card p {
            color: #666;
            font-size: 14px;
            margin: 5px 0;
        }
        .empty-message {
            text-align: center;
            color: #999;
            padding: 40px 20px;
            font-size: 16px;
        }
        @media (max-width: 768px) {
            header { flex-direction: column; gap: 15px; text-align: center; }
            header h1 { font-size: 20px; flex-direction: column; }
            .stats { grid-template-columns: 1fr; }
            .filters { justify-content: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>
                <img src="https://raw.githubusercontent.com/gulraizmalik/reddit-lead-detector/main/KMP-LOGO.png" 
                     alt="KMP Logo" 
                     onerror="this.style.display='none'">
                KMP REAL ESTATE
                <span style="font-size: 18px; color: #667eea;">Lead Detection Dashboard</span>
            </h1>
            <form action="/logout" method="post" style="margin: 0;">
                <button type="submit" class="logout-btn">Logout</button>
            </form>
        </header>

        <div class="stats">
            <div class="stat-card">
                <h3>📊 Total Leads</h3>
                <div class="value">0</div>
            </div>
            <div class="stat-card">
                <h3>🔥 Hot Leads</h3>
                <div class="value">0</div>
            </div>
            <div class="stat-card">
                <h3>🟡 Warm Leads</h3>
                <div class="value">0</div>
            </div>
            <div class="stat-card">
                <h3>⚪ Cold Leads</h3>
                <div class="value">0</div>
            </div>
        </div>

        <div class="section">
            <h2>🎯 Latest Leads</h2>
            <div class="filters">
                <button class="filter-btn active" onclick="showLeads('all')">📋 All</button>
                <button class="filter-btn" onclick="showLeads('hot')">🔥 Hot</button>
                <button class="filter-btn" onclick="showLeads('warm')">🟡 Warm</button>
                <button class="filter-btn" onclick="showLeads('cold')">⚪ Cold</button>
            </div>
            <div class="leads-list" id="leadsList">
                <div class="empty-message">
                    ✨ Leads will appear here once Reddit monitoring activates...
                </div>
            </div>
        </div>

        <div class="section">
            <h2>📈 Market Intelligence</h2>
            <div class="empty-message">
                🔍 Market data coming soon...
            </div>
        </div>
    </div>

    <script>
        function showLeads(type) {
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return LOGIN_HTML

@app.get("/login", response_class=HTMLResponse)
async def login():
    return LOGIN_HTML

@app.post("/auth")
async def auth(request: Request):
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        
        if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
            response = Response(content=DASHBOARD_HTML, media_type="text/html")
            response.set_cookie(key="auth", value="authenticated", httponly=True, max_age=86400)
            return response
        else:
            return HTMLResponse(LOGIN_HTML, status_code=401)
    except Exception as e:
        return HTMLResponse(LOGIN_HTML, status_code=400)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    auth = request.cookies.get("auth")
    if auth == "authenticated":
        return DASHBOARD_HTML
    else:
        return LOGIN_HTML

@app.post("/logout")
async def logout():
    response = Response(content=LOGIN_HTML, media_type="text/html")
    response.delete_cookie("auth")
    return response

@app.get("/health")
async def health():
    return {"status": "✅ Running"}

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
