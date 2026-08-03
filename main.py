import os
from fastapi import FastAPI
from fastapi.responses import FileResponse

app = FastAPI(title="KMP Real Estate Lead Detection")

@app.get("/dashboard")
async def get_dashboard():
    return FileResponse("dashboard.html", media_type="text/html")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "KMP Real Estate"}

@app.get("/")
async def root():
    return {"message": "KMP Real Estate System - Visit /dashboard"}

@app.get("/api/reddit/leads")
async def get_leads():
    return {"leads": [], "total": 0}

@app.get("/api/trends/market-signal")
async def market_signal():
    return {"overall_trend": "stable", "top_cities": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
