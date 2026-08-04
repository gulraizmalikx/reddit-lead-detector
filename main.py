import os
import json
import asyncio
import requests
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from anthropic import Anthropic
from pytrends.request import TrendReq

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DASHBOARD_USERNAME = "kmp"
DASHBOARD_PASSWORD = "Pakistan@2853"

app = FastAPI()
client = Anthropic()

leads_storage = {
    "leads": [
        {"id": "1", "title": "Luxury villa available in Downtown Dubai", "quality": "hot", "source": "Reddit", "timestamp": "14:32"},
        {"id": "2", "title": "Studio apartment for rent Dubai Marina", "quality": "warm", "source": "Reddit", "timestamp": "13:45"},
        {"id": "3", "title": "Looking to invest in UAE properties", "quality": "warm", "source": "Reddit", "timestamp": "12:20"},
    ],
    "stats": {"total": 3, "hot": 1, "warm": 2, "cold": 0}
}

market_trends = {
    "trends": [],
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
}

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP - Login</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center}.login-container{background:white;padding:40px;border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:100%;max-width:400px}.logo{text-align:center;margin-bottom:30px}.logo h1{color:#333;font-size:28px}.form-group{margin-bottom:20px}.form-group label{display:block;font-size:14px;color:#333;margin-bottom:8px;font-weight:600}input{width:100%;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px}input:focus{outline:none;border-color:#667eea}button{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:12px;border:none;border-radius:5px;font-size:16px;font-weight:600;cursor:pointer}</style></head><body><div class="login-container"><div class="logo"><h1>🏢 KMP REAL ESTATE</h1><p>Lead Detection</p></div><form method="post" action="/auth"><div class="form-group"><label>Username</label><input type="text" name="username" required></div><div class="form-group"><label>Password</label><input type="password" name="password" required></div><button type="submit">Login</button></form></div></body></html>"""

DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px}.container{max-width:1400px;margin:0 auto}header{background:white;padding:20px 30px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 5px 15px rgba(0,0,0,0.1)}header h1{font-size:28px;color:#333}button{background:#dc3545;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:30px}.stat-card{background:white;padding:30px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center}.stat-card h3{color:#666;font-size:14px;margin-bottom:15px}.stat-card .value{font-size:36px;font-weight:bold;color:#667eea}.section{background:white;padding:30px;border-radius:10px;margin-bottom:20px;box-shadow:0 5px 15px rgba(0,0,0,0.1)}.section h2{font-size:20px;margin-bottom:20px;color:#333}.filters{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}.filter-btn{padding:10px 20px;border:2px solid #ddd;background:white;border-radius:5px;cursor:pointer;font-size:14px;font-weight:600}.filter-btn.active{background:#667eea;color:white;border-color:#667eea}.lead-card{border:1px solid #eee;padding:15px;border-radius:5px;background:#f9f9f9;margin-bottom:10px}.lead-card h4{color:#333;margin-bottom:5px;word-break:break-word}.lead-card p{color:#666;font-size:13px;margin:3px 0}.trend-item{padding:15px;border-left:4px solid #667eea;background:#f0f5ff;margin-bottom:10px;border-radius:3px}.trend-item strong{color:#333}.empty{text-align:center;color:#999;padding:40px}</style></head><body><div class="container"><header><h1>🏢 KMP REAL ESTATE - Dashboard</h1><form action="/logout" method="post" style="margin:0"><button type="submit">Logout</button></form></header><div class="stats"><div class="stat-card"><h3>📊 Total Leads</h3><div class="value" id="total">0</div></div><div class="stat-card"><h3>🔥 Hot</h3><div class="value" id="hot">0</div></div><div class="stat-card"><h3>🟡 Warm</h3><div class="value" id="warm">0</div></div><div class="stat-card"><h3>⚪ Cold</h3><div class="value" id="cold">0</div></div></div><div class="section"><h2>🎯 Latest Leads</h2><div class="filters"><button class="filter-btn active" onclick="showLeads('all')">📋 All</button><button class="filter-btn" onclick="showLeads('hot')">🔥 Hot</button><button class="filter-btn" onclick="showLeads('warm')">🟡 Warm</button><button class="filter-btn" onclick="showLeads('cold')">⚪ Cold</button></div><div id="leadsContainer"></div></div><div class="section"><h2>📈 Market Intelligence</h2><div id="trendsContainer"></div></div></div><script>async function loadLeads(){try{const res=await fetch('/api/leads');const data=await res.json();document.getElementById('total').textContent=data.stats.total;document.getElementById('hot').textContent=data.stats.hot;document.getElementById('warm').textContent=data.stats.warm;document.getElementById('cold').textContent=data.stats.cold;const container=document.getElementById('leadsContainer');if(data.leads.length===0){container.innerHTML='<div class="empty">⏳ Monitoring leads...</div>';return}let html='';data.leads.forEach(lead=>{html+=`<div class="lead-card"><h4>${lead.title}</h4><p><strong>Quality:</strong> ${lead.quality.toUpperCase()}</p><p><strong>Source:</strong> ${lead.source}</p><p><strong>Time:</strong> ${lead.timestamp}</p></div>`;});container.innerHTML=html}catch(e){console.error(e)}}async function loadTrends(){try{const res=await fetch('/api/trends');const data=await res.json();const container=document.getElementById('trendsContainer');if(data.trends.length===0){container.innerHTML='<div class="empty">📊 Loading market trends...</div>';return}let html='';data.trends.forEach(trend=>{html+=`<div class="trend-item"><strong>🔍 ${trend.keyword}</strong><p>Interest: ${trend.value}% | Region: ${trend.region}</p></div>`;});container.innerHTML=html}catch(e){console.error(e)}}setInterval(loadLeads,5000);setInterval(loadTrends,30000);loadLeads();loadTrends()</script></body></html>"""

async def fetch_google_trends():
    """Fetch Google Trends data for Dubai real estate"""
    try:
        logger.info("📈 Fetching Google Trends...")
        pytrends = TrendReq(hl='en-US', tz=0)
        
        keywords = ["buy property Dubai", "real estate UAE", "villa Dubai", "apartment Dubai", "property investment UAE"]
        
        pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='AE')
        
        trends_data = pytrends.interest_over_time()
        
        market_trends["trends"] = []
        
        for keyword in keywords:
            try:
                pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='AE')
                data = pytrends.interest_over_time()
                
                if len(data) > 0:
                    latest_value = data[keyword].iloc[-1]
                    market_trends["trends"].append({
                        "keyword": keyword,
                        "value": int(latest_value),
                        "region": "UAE"
                    })
            except:
                pass
        
        market_trends["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        logger.info(f"✅ Trends updated: {len(market_trends['trends'])} keywords")
        
    except Exception as e:
        logger.error(f"Google Trends error: {e}")

@app.get("/", response_class=HTMLResponse)
async def root():
    return LOGIN_HTML

@app.post("/auth")
async def auth(request: Request):
    try:
        form_data = await request.form()
        username = form_data.get("username")
        password = form_data.get("password")
        
        if username == DASHBOARD_USERNAME and password == DASHBOARD_PASSWORD:
            response = Response(content=DASHBOARD_HTML, media_type="text/html")
            response.set_cookie(key="auth", value="ok", httponly=True, max_age=86400)
            logger.info(f"✅ Login successful for user: {username}")
            return response
        logger.warning(f"❌ Failed login attempt")
        return HTMLResponse(LOGIN_HTML, status_code=401)
    except Exception as e:
        logger.error(f"Auth error: {e}")
        return HTMLResponse(LOGIN_HTML, status_code=400)

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

@app.get("/api/leads")
async def get_leads():
    return leads_storage

@app.get("/api/trends")
async def get_trends():
    return market_trends

@app.get("/health")
async def health():
    logger.info("Health check")
    return {"status": "✅ Running"}

@app.on_event("startup")
async def startup():
    logger.info("🚀 APP STARTING")
    asyncio.create_task(trends_loop())

async def trends_loop():
    logger.info("📈 Trends loop started")
    while True:
        try:
            await fetch_google_trends()
        except Exception as e:
            logger.error(f"Trends loop error: {e}")
        logger.info("⏰ Waiting 3600 seconds (1 hour) until next trends update...")
        await asyncio.sleep(3600)

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
