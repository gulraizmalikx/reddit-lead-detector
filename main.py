import os
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse

DASHBOARD_USERNAME = "kmp"
DASHBOARD_PASSWORD = "Pakistan@2853"

app = FastAPI()

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP - Login</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center}.login-container{background:white;padding:40px;border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:100%;max-width:400px}.logo{text-align:center;margin-bottom:30px}.logo h1{color:#333;font-size:28px}.form-group{margin-bottom:20px}.form-group label{display:block;font-size:14px;color:#333;margin-bottom:8px;font-weight:600}input{width:100%;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px}input:focus{outline:none;border-color:#667eea}button{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:12px;border:none;border-radius:5px;font-size:16px;font-weight:600;cursor:pointer}</style></head><body><div class="login-container"><div class="logo"><h1>🏢 KMP REAL ESTATE</h1><p>Lead Detection</p></div><form method="post" action="/auth"><div class="form-group"><label>Username</label><input type="text" name="username" required></div><div class="form-group"><label>Password</label><input type="password" name="password" required></div><button type="submit">Login</button></form></div></body></html>"""

DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px}.container{max-width:1400px;margin:0 auto}header{background:white;padding:20px 30px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 5px 15px rgba(0,0,0,0.1)}header h1{font-size:28px;color:#333}header img{height:40px}button{background:#dc3545;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:30px}.stat-card{background:white;padding:30px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center}.stat-card h3{color:#666;font-size:14px;margin-bottom:15px}.stat-card .value{font-size:36px;font-weight:bold;color:#667eea}.section{background:white;padding:30px;border-radius:10px;margin-bottom:20px;box-shadow:0 5px 15px rgba(0,0,0,0.1)}.section h2{font-size:20px;margin-bottom:20px;color:#333}.filters{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}.filter-btn{padding:10px 20px;border:2px solid #ddd;background:white;border-radius:5px;cursor:pointer;font-size:14px;font-weight:600}.filter-btn.active{background:#667eea;color:white;border-color:#667eea}.empty{text-align:center;color:#999;padding:40px}</style></head><body><div class="container"><header><h1>🏢 KMP REAL ESTATE - Dashboard</h1><form action="/logout" method="post" style="margin:0"><button type="submit">Logout</button></form></header><div class="stats"><div class="stat-card"><h3>📊 Total Leads</h3><div class="value">0</div></div><div class="stat-card"><h3>🔥 Hot</h3><div class="value">0</div></div><div class="stat-card"><h3>🟡 Warm</h3><div class="value">0</div></div><div class="stat-card"><h3>⚪ Cold</h3><div class="value">0</div></div></div><div class="section"><h2>Latest Leads</h2><div class="filters"><button class="filter-btn active">📋 All</button><button class="filter-btn">🔥 Hot</button><button class="filter-btn">🟡 Warm</button><button class="filter-btn">⚪ Cold</button></div><div class="empty">Leads will appear when Reddit monitoring starts...</div></div></div></body></html>"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return LOGIN_HTML

@app.post("/auth")
async def auth(request: Request):
    form_data = await request.form()
    username = form_data.get("username")
    password = form_data.get("password")
    
    if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
        response = Response(content=DASHBOARD_HTML, media_type="text/html")
        response.set_cookie(key="auth", value="ok", httponly=True, max_age=86400)
        return response
    return HTMLResponse(LOGIN_HTML, status_code=401)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if request.cookies.get("auth") == "ok":
        return DASHBOARD_HTML
    return LOGIN_HTML

@app.post("/logout")
async def logout():
    response = Response(content=LOGIN_HTML, media_type="text/html")
    response.delete_cookie("auth")
    return response

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
