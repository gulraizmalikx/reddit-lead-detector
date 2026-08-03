from fastapi import FastAPI

app = FastAPI(title="Reddit Lead Detector", version="1.0.0")

@app.get("/")
async def root():
    return {"message": "Reddit Lead Detection System is Running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
