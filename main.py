"""
FastAPI Application for Reddit Lead Detection
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from reddit_endpoints import router
import os

# Create FastAPI app
app = FastAPI(
    title="Reddit Lead Detector",
    description="AI-powered lead detection from Reddit",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables
init_db()

# Include routers
app.include_router(router)

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "reddit-lead-detector"}

@app.get("/")
async def root():
    return {"message": "Reddit Lead Detection System is Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
