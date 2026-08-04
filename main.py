import os
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, Response, BackgroundTasks
from fastapi.responses import HTMLResponse
import praw
from anthropic import Anthropic

# Credentials
DASHBOARD_USERNAME = "kmp"
DASHBOARD_PASSWORD = "Pakistan@2853"
REDDIT_USERNAME = "FarBison1005"
REDDIT_PASSWORD = "Pakistan@2853"
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_API_KEY")

app = FastAPI()

# In-memory storage for leads
leads_storage = {
    "leads": [],
    "stats": {
        "total": 0,
        "hot": 0,
        "warm": 0,
        "cold": 0
    }
}

# Initialize Claude
client = Anthropic()

# Initialize Reddit
try:
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="KMP-RealEstateLeadDetector/1.0",
        username=REDDIT_USERNAME,
        password=REDDIT_PASSWORD
    )
except:
    reddit = None

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP - Login</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center}.login-container{background:white;padding:40px;border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:100%;max-width:400px}.logo{text-align:center;margin-bottom:30px}.logo h1{color:#333;font-size:28px}.form-group{margin-bottom:20px}.form-group label{display:block;font-size:14px;color:#333;margin-bottom:8px;font-weight:600}input{width:100%;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px}input:focus{outline:none;border-color:#667eea}button{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:12px;border:none;border-radius:5px;font-size:16px;font-weight:600;cursor:pointer}</style></head><body><div class="login-container"><div class="logo"><h1>🏢 KMP REAL ESTATE</h1><p>Lead Detection</p></div><form method="post" action="/auth"><div class="form-group"><label>Username</label><input type="text" name="username" required></div><div class="form-group"><label>Password</label><input type="password" name="password" required></div><button type="submit">Login</button></form></div></body></html>"""

DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px}.container{max-width:1400px;margin:0 auto}header{background:white;padding:20px 30px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 5px 15px rgba(0,0,0,0.1)}header h1{font-size:28px;color:#333}button{background:#dc3545;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:30px}.stat-card{background:white;padding:30px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center}.stat-card h3{color:#666;font-size:14px;margin-bottom:15px}.stat-card .value{font-size:36px;font-weight:bold;color:#667eea}.section{background:white;padding:30px;border-radius:10px;margin-bottom:20px;box-shadow:0 5px 15px rgba(0,0,0,0.1)}.section h2{font-size:20px;margin-bottom:20px;color:#333}.filters{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}.filter-btn{padding:10px 20px;border:2px solid #ddd;background:white;border-radius:5px;cursor:pointer;font-size:14px;font-weight:600}.filter-btn.active{background:#667eea;color:white;border-color:#667eea}.lead-card{border:1px solid #eee;padding:15px;border-radius:5px;background:#f9f9f9;margin-bottom:10px}.lead-card h4{color:#333;margin-bottom:5px}.lead-card p{color:#666;font-size:13px;margin:3px 0}.empty{text-align:center;color:#999;padding:40px}</style></head><body><div class="container"><header><h1>🏢 KMP REAL ESTATE - Dashboard</h1><form action="/logout" method="post" style="margin:0"><button type="submit">Logout</button></form></header><div class="stats"><div class="stat-card"><h3>📊 Total Leads</h3><div class="value" id="total">0</div></div><div class="stat-card"><h3>🔥 Hot</h3><div class="value" id="hot">0</div></div><div class="stat-card"><h3>🟡 Warm</h3><div class="value" id="warm">0</div></div><div class="stat-card"><h3>⚪ Cold</h3><div class="value" id="cold">0</div></div></div><div class="section"><h2>Latest Leads</h2><div class="filters"><button class="filter-btn active" onclick="showLeads('all')">📋 All</button><button class="filter-btn" onclick="showLeads('hot')">🔥 Hot</button><button class="filter-btn" onclick="showLeads('warm')">🟡 Warm</button><button class="filter-btn" onclick="showLeads('cold')">⚪ Cold</button></div><div id="leadsContainer" class="empty">Loading leads...</div></div></div><script>async function loadLeads(){try{const res=await fetch('/api/leads');const data=await res.json();document.getElementById('total').textContent=data.stats.total;document.getElementById('hot').textContent=data.stats.hot;document.getElementById('warm').textContent=data.stats.warm;document.getElementById('cold').textContent=data.stats.cold;const container=document.getElementById('leadsContainer');if(data.leads.length===0){container.innerHTML='<div class="empty">⏳ Monitoring Reddit for leads...</div>';return}let html='';data.leads.forEach(lead=>{html+=`<div class="lead-card"><h4>${lead.title}</h4><p><strong>Quality:</strong> ${lead.quality}</p><p><strong>Source:</strong> ${lead.source}</p><p><strong>Time:</strong> ${lead.timestamp}</p></div>`;});container.innerHTML=html}catch(e){console.error(e)}}function showLeads(type){document.querySelectorAll('.filter-btn').forEach(btn=>btn.classList.remove('active'));event.target.classList.add('active')}setInterval(loadLeads,5000);loadLeads()</script></body></html>"""

async def analyze_lead_with_claude(text):
    """Analyze a Reddit post to determine lead quality"""
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze this Reddit post for real estate lead quality in Dubai/UAE.
                    
Post: {text}

Respond in JSON format:
{{"quality": "hot|warm|cold", "confidence": 0-100, "reason": "brief reason"}}

Quality levels:
- HOT: Direct property inquiry or viewing request
- WARM: General interest in real estate, moving plans
- COLD: Tangential mention of property/real estate"""
                }
            ]
        )
        
        result_text = response.content[0].text
        try:
            return json.loads(result_text)
        except:
            return {"quality": "cold", "confidence": 0, "reason": "Parse error"}
    except Exception as e:
        return {"quality": "cold", "confidence": 0, "reason": str(e)}

async def monitor_reddit():
    """Background task to monitor Reddit for leads"""
    if not reddit:
        return
    
    subreddits = ["realestate", "dubai", "UAE", "property", "RealEstate_UAE"]
    
    try:
        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                for submission in subreddit.new(limit=10):
                    # Check if lead already exists
                    if any(lead["id"] == submission.id for lead in leads_storage["leads"]):
                        continue
                    
                    # Analyze with Claude
                    analysis = await analyze_lead_with_claude(
                        f"{submission.title}\n{submission.selftext[:500]}"
                    )
                    
                    if analysis["confidence"] > 40:
                        lead = {
                            "id": submission.id,
                            "title": submission.title,
                            "quality": analysis["quality"],
                            "source": f"r/{subreddit_name}",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "url": submission.url,
                            "confidence": analysis["confidence"]
                        }
                        
                        leads_storage["leads"].insert(0, lead)
                        if len(leads_storage["leads"]) > 100:
                            leads_storage["leads"] = leads_storage["leads"][:100]
                        
                        # Update stats
                        leads_storage["stats"]["total"] = len(leads_storage["leads"])
                        leads_storage["stats"]["hot"] = len([l for l in leads_storage["leads"] if l["quality"] == "hot"])
                        leads_storage["stats"]["warm"] = len([l for l in leads_storage["leads"] if l["quality"] == "warm"])
                        leads_storage["stats"]["cold"] = len([l for l in leads_storage["leads"] if l["quality"] == "cold"])
            except:
                pass
    except Exception as e:
        print(f"Reddit monitoring error: {e}")

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
            return response
        else:
            return HTMLResponse(LOGIN_HTML, status_code=401)
    except:
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

@app.get("/health")
async def health():
    return {"status": "✅ Running"}

@app.on_event("startup")
async def startup():
    """Start Reddit monitoring on app startup"""
    asyncio.create_task(monitor_reddit_loop())

async def monitor_reddit_loop():
    """Continuously monitor Reddit"""
    while True:
        await monitor_reddit()
        await asyncio.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT)
