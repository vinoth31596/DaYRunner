## Vinoth OS V2.2.0

V2.2.0 adds no-refresh activity deletion so deleting an item preserves the current scroll position.

# Vinoth OS V2.1.6

V2.1.4 adds no-reload task completion: checking/unchecking an activity saves in the background, updates the progress percentage immediately, and preserves the current scroll position. Normal form submission remains as a JavaScript-disabled fallback.

# Vinoth OS

Personal schedule + focus + history + Web Push reminders.

## V2 features
- Today schedule with dated completion history
- Configurable multi-session focus timer
- 7-day progress, focus minutes, gym count, study/gym streaks
- Per-activity reminders: at time / 5 / 10 / 30 minutes before
- Standards-based Web Push subscription and service worker
- Background server reminder scheduler (checks once per minute)
- SQLite locally; PostgreSQL-ready through `DATABASE_URL`
- PWA manifest + Home Screen support

## Run on Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
./generate_vapid_keys.sh
```
# Run on Same network
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
ipconfig getifaddr en0
http://192.168.1.25:8000
```

Copy `.env.example` to `.env`, then paste the two values printed by the key script. Set `VAPID_SUBJECT` to an email you control. Export the settings before launch:
```bash
set -a; source .env; set +a
python -m uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000.

## Local push caveat
Push APIs require a secure context. `localhost` is treated specially by browsers for development, but an iPhone visiting your Mac's plain `http://192.168...` address is not a production-quality push setup. For iPhone background reminders, deploy over HTTPS.

## iPhone
1. Deploy Vinoth OS to an HTTPS URL.
2. Open the URL on iPhone and add it to the Home Screen / open it as a web app.
3. Open Vinoth OS from the Home Screen.
4. Tap **Enable push reminders** and allow notifications.
5. Tap **Test notification**.
6. Enable Reminder on an activity and choose its offset.

The server must remain running for scheduled reminders. A production deployment should run a single dedicated scheduler/worker rather than starting a scheduler in every web-server replica.

## PostgreSQL
Set, for example:
`DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/focusflow`

## Deployment notes
Use any Python host that provides HTTPS and an always-on process. Keep `VAPID_PRIVATE_KEY` secret. Persist the database. For multiple web replicas, move `check_reminders` to one worker process/cron job to avoid duplicate scheduling.

## Not included yet
- Multi-user login/accounts
- Cloud hosting credentials or automatic AWS deployment
- Calendar sync
- AI schedule agent

Those are intentionally separate because they require your hosting/account choices and, for AI, an API provider/key.


## V2.1.5
- Schedule, history, and reminder notification times display in 12-hour AM/PM format.
- Times remain stored internally as HH:MM (24-hour) for reliable sorting and scheduling.


## Daily goals
Vinoth OS V2.2 adds whole-day tracking for **No Alcohol Today** and **Diet Done Today**. These are stored separately from timed schedule activities and appear in Week, Month, Year, and Start-to-date Progress with completed-day counts, adherence percentage, and current streaks.
