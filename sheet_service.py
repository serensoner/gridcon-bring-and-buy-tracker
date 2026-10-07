import csv
import io
import urllib.parse
import requests
import logging
from config import SHEET_ID, SHEET_TAB_NAME, SHEET_GID

logger = logging.getLogger("sheet_service")

AVAILABLE_TABS = [
    {"name": "Raw Data 7", "gid": "1235113395"},
    {"name": "Available Items", "gid": "1988649514"},
    {"name": "Alphabetical", "gid": "36294078"},
    {"name": "Price Low-High", "gid": "2040633502"},
    {"name": "Price High-Low", "gid": "1050769963"},
    {"name": "Read this first", "gid": "867825655"},
]

def fetch_sheet_csv(sheet_id: str = SHEET_ID, gid: str = SHEET_GID, tab_name: str = SHEET_TAB_NAME) -> str:
    """
    Fetches raw CSV text from Google Sheets export URL.
    Attempts using GID first, falls back to tab_name parameter if GID fails.
    """
    # Ensure default GID if empty
    effective_gid = gid if (gid and gid not in ["undefined", "null", ""]) else SHEET_GID

    urls_to_try = [
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={effective_gid}"
    ]
    if tab_name:
        encoded_name = urllib.parse.quote(tab_name)
        urls_to_try.append(f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded_name}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    last_err = None
    for url in urls_to_try:
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200 and resp.text.strip():
                return resp.text
        except Exception as e:
            last_err = e
            logger.warning(f"Failed fetching sheet from {url}: {e}")

    raise RuntimeError(f"Unable to fetch Google Sheet data. Last error: {last_err}")

def parse_sheet_data(csv_text: str) -> dict:
    """
    Parses CSV content into structured JSON response with column list and list of row dicts.
    """
    lines = [line for line in csv_text.strip().splitlines() if line.strip()]
    if not lines:
        return {"columns": [], "rows": [], "total_count": 0}

    reader = csv.reader(io.StringIO("\n".join(lines)))
    rows_list = list(reader)

    if not rows_list:
        return {"columns": [], "rows": [], "total_count": 0}

    headers = [col.strip() for col in rows_list[0]]
    parsed_rows = []

    for index, row in enumerate(rows_list[1:], start=1):
        if not any(cell.strip() for cell in row):
            continue

        row_dict = {"_row_id": index}
        for col_idx, header_name in enumerate(headers):
            cell_value = row[col_idx].strip() if col_idx < len(row) else ""
            row_dict[header_name] = cell_value

        parsed_rows.append(row_dict)

    return {
        "columns": headers,
        "rows": parsed_rows,
        "total_count": len(parsed_rows)
    }

def get_sheet_data(sheet_id: str = SHEET_ID, gid: str = SHEET_GID, tab_name: str = SHEET_TAB_NAME) -> dict:
    effective_gid = gid if (gid and gid not in ["undefined", "null", ""]) else SHEET_GID
    
    # Resolve tab name for given GID
    matched_tab = next((t for t in AVAILABLE_TABS if t["gid"] == effective_gid), None)
    effective_tab_name = matched_tab["name"] if matched_tab else tab_name

    csv_content = fetch_sheet_csv(sheet_id, effective_gid, effective_tab_name)
    data = parse_sheet_data(csv_content)
    data["sheet_id"] = sheet_id
    data["tab_name"] = effective_tab_name
    data["gid"] = effective_gid
    data["available_tabs"] = AVAILABLE_TABS
    return data
