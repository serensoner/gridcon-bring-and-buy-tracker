import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

import config
from sheet_service import get_sheet_data, AVAILABLE_TABS
from scheduler import start_scheduler, stop_scheduler, check_sheet_job
from db import get_last_sync_info
from config import DATABASE_PATH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting GridCon Bring & Buy Tracker service...")
    start_scheduler()
    yield
    logger.info("Stopping background scheduler...")
    stop_scheduler()

app = FastAPI(
    title="GridCon Bring & Buy Tracker",
    description="Mobile-friendly viewer and Slack notifier for Google Sheet entries",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for all origins to prevent browser fetch blocking
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static directory for frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "GridCon Bring & Buy API is running. Frontend index.html not found."}

@app.get("/api/data")
def api_get_data(
    gid: str = Query(default=config.SHEET_GID),
    tab_name: str = Query(default=config.SHEET_TAB_NAME)
):
    try:
        data = get_sheet_data(config.SHEET_ID, gid, tab_name)
        data["last_sync"] = get_last_sync_info(DATABASE_PATH)
        return data
    except Exception as e:
        logger.error(f"Error serving /api/data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
def api_get_config():
    return {
        "sheet_id": config.SHEET_ID,
        "sheet_tab_name": config.SHEET_TAB_NAME,
        "sheet_gid": config.SHEET_GID,
        "poll_interval_seconds": config.POLL_INTERVAL_SECONDS,
        "available_tabs": AVAILABLE_TABS,
        "slack_configured": bool(config.SLACK_WEBHOOK_URL),
        "last_sync": get_last_sync_info(DATABASE_PATH)
    }

@app.post("/api/trigger-check")
def api_trigger_check():
    result = check_sheet_job(is_manual=True)
    return result

@app.get("/api/health")
def api_health():
    return {"status": "ok", "last_sync": get_last_sync_info(DATABASE_PATH)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
