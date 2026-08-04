import os
import json
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from pytrends.request import TrendReq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DASHBOARD_USERNAME = "kmp"
DASHBOARD_PASSWORD = "Pakistan@2853"

app = FastAPI()

market_data = {
    "location": "Bur Dubai",
    "total_interest": 0,
    "trend_direction": "→",
    "trend_percent": 0,
    "comparisons": [],
    "trending_keywords": [],
    "property_types": [],
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
}

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP - Login</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center}.login-container{background:white;padding:40px;border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:100%;max-width:400px}.logo{text-align:center;margin-bottom:30px}.logo h1{color:#333;font-size:28px}.form-group{margin-bottom:20px}.form-group label{display:block;font-size:14px;color:#333;margin-bottom:8px;font-weight:600}input{width:100%;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px}input:focus{outline:none;border-color:#667eea}button{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:12px;border:none;border-radius:5px;font-size:16px;font-weight:600;cursor:pointer}</style></head><body><div class="login-container"><div class="logo"><h1>🏢 KMP REAL ESTATE</h1><p>Market Intelligence</p></div><form method="post" action="/auth"><div class="form-group"><label>Username</label><input type="text" name="username" required></div><div class="form-group"><label>Password</label><input type="password" name="password" required></div><button type="submit">Login</button></form></div></body></html>"""

DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px}.container{max-width:1200px;margin:0 auto}header{background:white;padding:20px 30px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 5px 15px rgba(0,0,0,0.1)}header h1{font-size:28px;color:#333}button{background:#dc3545;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:30px}.stat-card{background:white;padding:30px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center}.stat-card h3{color:#666;font-size:14px;margin-bottom:15px}.stat-card .value{font-size:36px;font-weight:bold;color:#667eea}.section{background:white;padding:30px;border-radius:10px;margin-bottom:20px;box-shadow:0 5px 15px rgba(0,0,0,0.1)}.section h2{font-size:20px;margin-bottom:20px;color:#333}.location-selector{margin-bottom:20px}.location-selector select{padding:10px;border:1px solid #ddd;border-radius:5px;font-size:14px;width:100%;max-width:300px}.comparison-item{padding:15px;border-left:4px solid #667eea;background:#f0f5ff;margin-bottom:10px;border-radius:3px}.comparison-label{font-weight:bold;color:#333}.comparison-value{font-size:18px;color:#667eea;font-weight:bold}.trending-keyword{display:inline-block;background:#667eea;color:white;padding:8px 12px;margin:5px;border-radius:20px;font-size:13px}.keyword-trend{margin-left:5px;font-weight:bold}.trend-up{color:#28a745}.trend-down{color:#dc3545}.trend-stable{color:#ffc107}.property-type{padding:12px;background:#f9f9f9;border-left:3px solid #667eea;margin-bottom:8px;border-radius:3px}.empty{text-align:center;color:#999;padding:40px}.authenticity-badge{background:#d4edda;color:#155724;padding:10px 15px;border-radius:5px;margin-bottom:15px;font-size:13px;border-left:3px solid #28a745}</style></head><body><div class="container"><header><h1>🏢 KMP REAL ESTATE - Authentic Market Intelligence</h1><form action="/logout" method="post" style="margin:0"><button type="submit">Logout</button></form></header><div class="stats"><div class="stat-card"><h3>📊 Search Interest</h3><div class="value" id="total-interest">-</div></div><div class="stat-card"><h3>📈 Trend Direction</h3><div class="value" id="trend-direction">-</div></div><div class="stat-card"><h3>📍 Current Location</h3><div class="value" id="current-location">-</div></div><div class="stat-card"><h3>🔍 Last Updated</h3><div id="last-updated" style="font-size:14px;color:#667eea">-</div></div></div><div class="section"><div class="authenticity-badge">✅ Data Source: Google Trends (100% Authentic) | No sample data</div><h2>📍 Select Location</h2><div class="location-selector"><select id="locationSelect" onchange="loadLocationData()"><option value="">-- Select a Location --</option><option value="Bur Dubai">Bur Dubai</option><option value="Mankhool">Mankhool</option><option value="Downtown Dubai">Downtown Dubai</option><option value="Dubai Marina">Dubai Marina</option></select></div></div><div class="section"><h2>🏠 Property Type Search Volume</h2><div id="propertyTypes"></div></div><div class="section"><h2>⚖️ Location Comparisons</h2><p style="color:#666;font-size:13px;margin-bottom:15px;">Relative search volume comparison (higher = more searches)</p><div id="comparisons"></div></div><div class="section"><h2>🔥 Trending Keywords</h2><p style="color:#666;font-size:13px;margin-bottom:15px;">What people are actually searching for in this location</p><div id="trendingKeywords"></div></div></div><script>async function loadLocationData(){const location=document.getElementById('locationSelect').value;if(!location){document.getElementById('propertyTypes').innerHTML='<p class="empty">Select a location first</p>';return}try{const res=await fetch(`/api/market-data?location=${location}`);const data=await res.json();document.getElementById('total-interest').textContent=data.total_interest;document.getElementById('trend-direction').textContent=data.trend_direction+' '+data.trend_percent+'%';document.getElementById('current-location').textContent=location;document.getElementById('last-updated').textContent=data.last_updated;const propDiv=document.getElementById('propertyTypes');propDiv.innerHTML='';data.property_types.forEach(prop=>{const div=document.createElement('div');div.className='property-type';div.innerHTML=`<strong>${prop.type}</strong><span class="keyword-trend trend-${prop.trend.toLowerCase()}"> ${prop.trend}</span><div style="font-size:13px;color:#666;margin-top:5px">Interest: ${prop.interest}</div>`;propDiv.appendChild(div)});const compDiv=document.getElementById('comparisons');compDiv.innerHTML='';data.comparisons.forEach(comp=>{const div=document.createElement('div');div.className='comparison-item';div.innerHTML=`<div class="comparison-label">${comp.location1} vs ${comp.location2}</div><div class="comparison-value">${comp.location1}: ${comp.value1} | ${comp.location2}: ${comp.value2}</div>`;compDiv.appendChild(div)});const keyDiv=document.getElementById('trendingKeywords');keyDiv.innerHTML='';data.trending_keywords.forEach(keyword=>{const span=document.createElement('span');span.className='trending-keyword';span.innerHTML=`${keyword.keyword} <span class="keyword-trend trend-${keyword.trend.toLowerCase()}">${keyword.trend}</span>`;keyDiv.appendChild(span)})}catch(e){console.error(e)}}loadLocationData()</script></body></html>"""

async def fetch_authentic_trends(location):
    """Fetch authentic Google Trends data"""
    logger.info(f"📊 Fetching authentic Google Trends for: {location}")
    
    try:
        pytrends = TrendReq(hl='en-US', tz=0)
        
        # Property type searches
        property_keywords = [
            f"villa {location}",
            f"apartment {location}",
            f"studio {location}",
            f"townhouse {location}"
        ]
        
        # Build payload for property types
        pytrends.build_payload(property_keywords, cat=0, timeframe='now 7-d', geo='AE')
        interest_data = pytrends.interest_over_time()
        
        property_types = []
        for keyword in property_keywords:
            if keyword in interest_data.columns:
                latest_value = int(interest_data[keyword].iloc[-1])
                prev_value = int(interest_data[keyword].iloc[-8]) if len(interest_data) > 7 else latest_value
                trend = "↑" if latest_value > prev_value else ("↓" if latest_value < prev_value else "→")
                percent = abs(latest_value - prev_value)
                
                property_types.append({
                    "type": keyword.split()[0].capitalize(),
                    "interest": latest_value,
                    "trend": trend,
                    "percent": percent
                })
        
        # Get total interest
        total_interest = sum([p["interest"] for p in property_types])
        
        # Get trending keywords
        related_keywords = []
        try:
            pytrends.build_payload([f"property {location}"], cat=0, timeframe='now 7-d', geo='AE')
            related = pytrends.related_queries()
            if related and "property " + location in related:
                top_queries = related["property " + location]["top"][:5]
                for _, row in top_queries.iterrows():
                    related_keywords.append({
                        "keyword": row['query'],
                        "trend": "↑" if row['value'] > 50 else ("↓" if row['value'] < 30 else "→")
                    })
        except:
            pass
        
        # Comparisons with other locations
        comparisons = []
        other_locations = ["Mankhool", "Downtown Dubai", "Dubai Marina"]
        for other_loc in other_locations:
            if other_loc != location:
                try:
                    pytrends.build_payload(
                        [f"property {location}", f"property {other_loc}"],
                        cat=0, timeframe='now 7-d', geo='AE'
                    )
                    comp_data = pytrends.interest_over_time()
                    val1 = int(comp_data[f"property {location}"].iloc[-1]) if f"property {location}" in comp_data.columns else 0
                    val2 = int(comp_data[f"property {other_loc}"].iloc[-1]) if f"property {other_loc}" in comp_data.columns else 0
                    
                    comparisons.append({
                        "location1": location,
                        "location2": other_loc,
                        "value1": val1,
                        "value2": val2
                    })
                except:
                    pass
        
        # Determine overall trend
        overall_trend = "→"
        trend_percent = 0
        if property_types:
            up_count = sum(1 for p in property_types if p["trend"] == "↑")
            down_count = sum(1 for p in property_types if p["trend"] == "↓")
            if up_count > down_count:
                overall_trend = "↑"
                trend_percent = sum(p["percent"] for p in property_types if p["trend"] == "↑") // len(property_types)
            elif down_count > up_count:
                overall_trend = "↓"
                trend_percent = sum(p["percent"] for p in property_types if p["trend"] == "↓") // len(property_types)
        
        market_data["location"] = location
        market_data["total_interest"] = total_interest
        market_data["property_types"] = property_types
        market_data["trending_keywords"] = related_keywords
        market_data["comparisons"] = comparisons
        market_data["trend_direction"] = overall_trend
        market_data["trend_percent"] = trend_percent
        market_data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        logger.info(f"✅ Authentic trends fetched: {total_interest} total interest")
        
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
            logger.info("✅ Login successful")
            return response
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

@app.get("/api/market-data")
async def get_market_data(location: str = ""):
    if location:
        await fetch_authentic_trends(location)
    return market_data

@app.get("/health")
async def health():
    return {"status": "✅ Running"}

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
