import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

SHEET_ID = os.getenv("SHEET_ID")
SHEET_TAB_NAME = os.getenv("SHEET_TAB_NAME")
SHEET_GID = os.getenv("SHEET_GID")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/tracker.db")
PORT = int(os.getenv("PORT", "8000"))
