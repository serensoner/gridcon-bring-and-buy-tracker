import logging
from apscheduler.schedulers.background import BackgroundScheduler
import config
from sheet_service import get_sheet_data
from db import is_db_empty, process_entries, log_sync
from config import DATABASE_PATH
from slack_notifier import notify_new_entries

logger = logging.getLogger("scheduler")

_scheduler = None

def check_sheet_job(is_manual: bool = False) -> dict:
    """
    Background worker job:
    1. Fetches sheet rows.
    2. Compares against SQLite database.
    3. Identifies new additions.
    4. Posts Slack alerts for new additions.
    """
    logger.info(f"Running sheet check job (manual={is_manual})...")
    try:
        data = get_sheet_data(config.SHEET_ID, config.SHEET_GID, config.SHEET_TAB_NAME)
        rows = data.get("rows", [])

        # Check if DB is being initialized for the very first time
        initial_seed = is_db_empty(DATABASE_PATH)
        if initial_seed:
            logger.info(f"Initial DB seed: recording {len(rows)} existing items without firing Slack alerts.")

        new_entries = process_entries(DATABASE_PATH, rows, is_initial_seed=initial_seed)

        if not initial_seed and new_entries:
            notify_new_entries(new_entries)

        log_sync(DATABASE_PATH, total_items=len(rows), new_items=len(new_entries), status="SUCCESS")

        result = {
            "status": "SUCCESS",
            "total_items": len(rows),
            "new_items": len(new_entries),
            "initial_seed": initial_seed
        }
        logger.info(f"Sheet check finished: {result}")
        return result
    except Exception as e:
        logger.error(f"Error during sheet check job: {e}", exc_info=True)
        log_sync(DATABASE_PATH, total_items=0, new_items=0, status="ERROR", error_message=str(e))
        return {
            "status": "ERROR",
            "error": str(e)
        }

def start_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        logger.info("Scheduler already running.")
        return

    _scheduler = BackgroundScheduler()
    # Run every POLL_INTERVAL_SECONDS (default: 300 seconds = 5 minutes)
    _scheduler.add_job(
        check_sheet_job,
        'interval',
        seconds=config.POLL_INTERVAL_SECONDS,
        id='sheet_check_job',
        replace_existing=True
    )
    _scheduler.start()
    logger.info(f"Background scheduler started. Checking sheet every {config.POLL_INTERVAL_SECONDS} seconds (5 minutes).")

    # Perform initial check on startup
    check_sheet_job(is_manual=False)

def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        logger.info("Scheduler stopped.")
