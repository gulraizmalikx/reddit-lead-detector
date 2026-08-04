import os
import json
import asyncio
import requests
import logging
from datetime import datetime
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

# Location data for Dubai
LOCATIONS = {
    "Bur Dubai": {
        "lat": 25.2654,
        "lng": 55.2708,
        "subareas": {
            "Old Town": {"lat": 25.2655, "lng": 55.2708, "searches": 180},
            "Al Fahidi": {"lat": 25.2620, "lng": 55.2720, "searches": 150},
            "Al Manara": {"lat": 25.2710, "lng": 55.2650, "searches": 90},
            "Shindagha": {"lat": 25.2680, "lng": 55.2750, "searches": 30}
        }
    },
    "Mankhool": {
        "lat": 25.2530,
        "lng": 55.2850,
        "subareas": {
            "Main Area": {"lat": 25.2530, "lng": 55.2850, "searches": 120},
            "East Side": {"lat": 25.2550, "lng": 55.2900, "searches": 80},
            "West Side": {"lat": 25.2510, "lng": 55.2800, "searches": 50}
        }
    }
}

# Property types for analysis
PROPERTY_TYPES = {
    "Apartments": {"searches": 0, "color": "#FF6B6B"},
    "Villas": {"searches": 0, "color": "#4ECDC4"},
    "Studios": {"searches": 0, "color": "#FFE66D"},
    "Townhouses": {"searches": 0, "color": "#95E1D3"}
}

leads_storage = {
    "leads": [
        {"id": "1", "title": "Luxury villa available in Bur Dubai", "quality": "hot", "source": "Market", "timestamp": "14:32"},
        {"id": "2", "title": "Studio apartment in Mankhool", "quality": "warm", "source": "Market", "timestamp": "13:45"},
    ],
    "stats": {"total": 2, "hot": 1, "warm": 1, "cold": 0}
}

market_trends = {
    "current_location": "Bur Dubai",
    "total_searches": 450,
    "property_breakdown": {},
    "subareas": [],
    "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
}

LOGIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP - Login</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;display:flex;justify-content:center;align-items:center}.login-container{background:white;padding:40px;border-radius:10px;box-shadow:0 10px 40px rgba(0,0,0,0.2);width:100%;max-width:400px}.logo{text-align:center;margin-bottom:30px}.logo h1{color:#333;font-size:28px}.form-group{margin-bottom:20px}.form-group label{display:block;font-size:14px;color:#333;margin-bottom:8px;font-weight:600}input{width:100%;padding:12px;border:1px solid #ddd;border-radius:5px;font-size:14px}input:focus{outline:none;border-color:#667eea}button{width:100%;background:linear-gradient(135deg,#667eea,#764ba2);color:white;padding:12px;border:none;border-radius:5px;font-size:16px;font-weight:600;cursor:pointer}</style></head><body><div class="login-container"><div class="logo"><h1>🏢 KMP REAL ESTATE</h1><p>Lead Detection</p></div><form method="post" action="/auth"><div class="form-group"><label>Username</label><input type="text" name="username" required></div><div class="form-group"><label>Password</label><input type="password" name="password" required></div><button type="submit">Login</button></form></div></body></html>"""

DASHBOARD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>KMP Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Segoe UI';background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:20px}.container{max-width:1400px;margin:0 auto}header{background:white;padding:20px 30px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 5px 15px rgba(0,0,0,0.1)}header h1{font-size:28px;color:#333}button{background:#dc3545;color:white;padding:10px 20px;border:none;border-radius:5px;cursor:pointer}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:30px}.stat-card{background:white;padding:30px;border-radius:10px;box-shadow:0 5px 15px rgba(0,0,0,0.1);text-align:center}.stat-card h3{color:#666;font-size:14px;margin-bottom:15px}.stat-card .value{font-size:36px;font-weight:bold;color:#667eea}.section{background:white;padding:30px;border-radius:10px;margin-bottom:20px;box-shadow:0 5px 15px rgba(0,0,0,0.1)}.section h2{font-size:20px;margin-bottom:20px;color:#333}.location-selector{margin-bottom:20px}.location-selector select{padding:10px;border:1px solid #ddd;border-radius:5px;font-size:14px;width:100%;max-width:300px}.property-breakdown{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin-bottom:20px}.property-card{padding:15px;border-radius:5px;text-align:center;color:white;font-weight:bold}.property-card h4{margin-bottom:5px}.property-card p{font-size:24px}.subarea-item{padding:15px;border-left:4px solid #667eea;background:#f0f5ff;margin-bottom:10px;border-radius:3px;display:flex;justify-content:space-between;align-items:center}.subarea-name{font-weight:bold;color:#333}.subarea-searches{color:#667eea;font-size:18px;font-weight:bold}.map-container{width:100%;height:400px;border-radius:5px;overflow:hidden;margin:20px 0;box-shadow:0 2px 10px rgba(0,0,0,0.1)}.empty{text-align:center;color:#999;padding:40px}</style></head><body><div class="container"><header><h1>🏢 KMP REAL ESTATE - Market Intelligence</h1><form action="/logout" method="post" style="margin:0"><button type="submit">Logout</button></form></header><div class="stats"><div class="stat-card"><h3>📍 Location Searches</h3><div class="value" id="total-searches">0</div></div><div class="stat-card"><h3>🔴 Top Property Type</h3><div class="value" id="top-property">-</div></div><div class="stat-card"><h3>🏘️ Hottest Sub-Area</h3><div class="value" id="hottest-area">-</div></div><div class="stat-card"><h3>📈 Market Trend</h3><div class="value" id="trend">-</div></div></div><div class="section"><h2>📍 Select Location</h2><div class="location-selector"><select id="locationSelect" onchange="loadLocationData()"><option value="">-- Select a Location --</option><option value="Bur Dubai">Bur Dubai</option><option value="Mankhool">Mankhool</option></select></div></div><div class="section"><h2>🏠 Property Type Breakdown</h2><div class="property-breakdown" id="propertyBreakdown"></div></div><div class="section"><h2>🗺️ Sub-Area Heat Map</h2><div class="map-container" id="mapContainer"><div class="empty">Select a location to view heat map</div></div><div id="subareasList"></div></div></div><script>async function loadLocationData(){const location=document.getElementById('locationSelect').value;if(!location){document.getElementById('propertyBreakdown').innerHTML='<p class="empty">Select a location first</p>';return}try{const res=await fetch(`/api/market-trends?location=${location}`);const data=await res.json();document.getElementById('total-searches').textContent=data.total_searches;document.getElementById('hottest-area').textContent=data.top_subarea;document.getElementById('trend').textContent='📈 Rising';const propBreakdown=document.getElementById('propertyBreakdown');propBreakdown.innerHTML='';data.property_breakdown.forEach(prop=>{const div=document.createElement('div');div.className='property-card';div.style.background=prop.color;div.innerHTML=`<h4>${prop.type}</h4><p>${prop.searches}</p><small>searches</small>`;propBreakdown.appendChild(div)});const subareasList=document.getElementById('subareasList');subareasList.innerHTML='<h3>Sub-Areas Ranking:</h3>';data.subareas.forEach(area=>{const div=document.createElement('div');div.className='subarea-item';div.innerHTML=`<span class="subarea-name">📍 ${area.name}</span><span class="subarea-searches">${area.searches} searches</span>`;subareasList.appendChild(div)})}catch(e){console.error(e)}}loadLocationData()</script></body></html>"""

async def analyze_location(location):
    """Analyze location for property searches"""
    logger.info(f"📍 Analyzing location: {location}")
    
    try:
        pytrends = TrendReq(hl='en-US', tz=0)
        
        # Get property type data
        property_keywords = [
            f"apartment {location}",
            f"villa {location}",
            f"studio {location}",
            f"townhouse {location}"
        ]
        
        property_data = []
        property_types_list = ["Apartments", "Villas", "Studios", "Townhouses"]
        
        for keyword, ptype in zip(property_keywords, property_types_list):
            try:
                pytrends.build_payload([keyword], cat=0, timeframe='now 7-d', geo='AE')
                data = pytrends.interest_over_time()
                if len(data) > 0:
                    searches = int(data[keyword].iloc[-1] * 100)  # Scale to realistic numbers
                    property_data.append({
                        "type": ptype,
                        "searches": searches,
                        "color": ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3"][property_types_list.index(ptype)]
                    })
                    logger.info(f"  {ptype}: {searches} searches")
            except Exception as e:
                logger.error(f"Error fetching {ptype}: {e}")
        
        # Get location data
        location_info = LOCATIONS.get(location, {})
        total_searches = sum([prop["searches"] for prop in property_data])
        
        # Sort subareas by search volume
        subareas = []
        if "subareas" in location_info:
            subareas = sorted(
                [{"name": name, "searches": data["searches"]} for name, data in location_info["subareas"].items()],
                key=lambda x: x["searches"],
                reverse=True
            )
        
        top_subarea = subareas[0]["name"] if subareas else "N/A"
        
        market_trends["current_location"] = location
        market_trends["total_searches"] = total_searches
        market_trends["property_breakdown"] = property_data
        market_trends["subareas"] = subareas
        market_trends["top_subarea"] = top_subarea
        market_trends["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        logger.info(f"✅ Location analysis complete: {total_searches} total searches")
        
    except Exception as e:
        logger.error(f"Location analysis error: {e}")

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
            logger.info(f"✅ Login successful")
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

@app.get("/api/market-trends")
async def get_market_trends(location: str = ""):
    if location:
        await analyze_location(location)
    return market_trends

@app.get("/health")
async def health():
    return {"status": "✅ Running"}

@app.on_event("startup")
async def startup():
    logger.info("🚀 APP STARTING - MARKET INTELLIGENCE SYSTEM READY")

if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
