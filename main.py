import os
import threading
import logging
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from database import init_db, SessionLocal
from reddit_endpoints import router as reddit_router
from reddit_monitor import start_reddit_monitoring
from google_trends_monitor import start_google_trends_monitoring

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
try:
    init_db()
    logger.info("✅ Database initialized")
except Exception as e:
    logger.warning(f"⚠️ Database already initialized or error: {e}")

# Start monitoring in background threads (non-blocking)
def start_background_monitors():
    """Start Reddit and Google Trends monitoring"""
    try:
        reddit_thread = threading.Thread(target=start_reddit_monitoring, daemon=True)
        reddit_thread.start()
        logger.info("✅ Reddit monitoring started")
    except Exception as e:
        logger.error(f"❌ Reddit monitoring error: {e}")
    
    try:
        trends_thread = threading.Thread(target=start_google_trends_monitoring, daemon=True)
        trends_thread.start()
        logger.info("✅ Google Trends monitoring started")
    except Exception as e:
        logger.error(f"❌ Google Trends monitoring error: {e}")

# Create FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_background_monitors()
    yield
    # Shutdown
    logger.info("Application shutting down")

app = FastAPI(title="KMP Real Estate Lead Detection", lifespan=lifespan)

# Include routers
app.include_router(reddit_router, prefix="/api/reddit")

# Dashboard route
@app.get("/dashboard")
async def get_dashboard():
    """Serve the dashboard HTML"""
    return FileResponse("dashboard.html", media_type="text/html")

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "KMP Real Estate Lead Detection",
        "version": "1.0.0"
    }

# Root redirect
@app.get("/")
async def root():
    return {"message": "KMP Real Estate Lead Detection System", "docs": "/docs", "dashboard": "/dashboard"}

# Serve static files (optional, for future use)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"⚠️ Static files directory not found: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
