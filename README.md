# GridCon Bring & Buy Tracker

Mobile-friendly web viewer and automatic background Slack notifier for the **GridCon Bring and Buy** Google Sheet (`Raw Data 7` tab).

## Features

- 🎲 **Google Sheet Integration**: Tracks public sheet (`1P8DKWL2fzl2THw9fHdvpSisEj5V6st8rPzVHHq2s2iE`) with tab auto-detection (defaulting to `Raw Data 7`).
- 📱 **Mobile-Friendly UI**: Card layout optimized for mobile screens, responsive data table view for desktop.
- 🔍 **Dynamic Filtering & Sorting**: Instant real-time search across all columns, column-specific dropdown filters, sort by price/timestamp/name, and hide sold items toggle.
- ⚡ **5-Minute Background Job**: Automatically re-checks the sheet every 5 minutes using APScheduler.
- 🔔 **Slack Notifications**: Detects NEW additions (excluding existing entries via SQLite hashing) and sends formatted Slack alerts to your webhook.
- 🐳 **Docker Ready**: Includes `Dockerfile` and `docker-compose.yml` with persistent volume support.

---

## Local Development (Uvicorn)

1. **Install dependencies**:
   ```bash
   py -3 -m pip install -r requirements.txt
   ```

2. **Run locally**:
   ```bash
   py -3 main.py
   ```
   or
   ```bash
   py -3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Open Web Browser**:
   Navigate to `http://localhost:8000`

---

## Remote Deployment (Docker)

```bash
docker compose up -d --build
```
The app will run on port `8000` with persistent SQLite storage at `gridconbb_data`.
