import requests
import logging
from config import SLACK_WEBHOOK_URL

logger = logging.getLogger("slack_notifier")

def send_slack_message(message: str, webhook_url: str = None):
    url = webhook_url or SLACK_WEBHOOK_URL
    if not url:
        logger.warning("No Slack webhook URL configured.")
        return
    try:
        response = requests.post(url, json={'text': message}, timeout=10)
        response.raise_for_status()
        logger.info("Slack message sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send Slack message: {e}")

def format_new_entry_message(entry: dict) -> str:
    game = entry.get("What game are you selling?") or entry.get("Game") or "Unknown Game"
    seller = entry.get("Your name") or entry.get("Seller") or "Unknown Seller"
    price = entry.get("Price") or entry.get("Price (UKP)") or "N/A"
    condition = entry.get("Condition:") or entry.get("Condition") or "N/A"
    notes = entry.get("Notes") or ""
    contact = entry.get("Your contact details (phone number / email address)") or entry.get("Contact") or ""
    timestamp = entry.get("Timestamp") or ""

    lines = [f"🎲 *New Bring & Buy Entry Added!*"]
    lines.append(f"• *Game*: *{game}*")
    lines.append(f"• *Price*: {price}")
    lines.append(f"• *Seller*: {seller}")
    if condition:
        lines.append(f"• *Condition*: {condition}")
    if contact:
        lines.append(f"• *Contact*: {contact}")
    if notes:
        lines.append(f"• *Notes*: {notes}")
    if timestamp:
        lines.append(f"• *Added*: {timestamp}")

    return "\n".join(lines)

def notify_new_entries(new_entries: list[dict]):
    if not new_entries:
        return

    logger.info(f"Notifying Slack for {len(new_entries)} new additions.")
    for entry in new_entries:
        msg = format_new_entry_message(entry)
        send_slack_message(msg)
