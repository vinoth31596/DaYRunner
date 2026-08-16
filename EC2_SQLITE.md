# Vinoth OS — EC2 + SQLite

Vinoth OS now defaults to a persistent SQLite file at `data/vinoth_os.db`.
On EC2, keep the project under `/opt/vinoth-os` so the DB lives at `/opt/vinoth-os/data/vinoth_os.db` on the EBS volume.

## First run on Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
The database is created automatically the first time the app starts.

## EC2 production process
Copy the project to `/opt/vinoth-os`, create `.venv`, install requirements, then install `vinoth-os.service` into `/etc/systemd/system/` and run:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now vinoth-os
sudo systemctl status vinoth-os
```

## Backup
```bash
PROJECT_DIR=/opt/vinoth-os ./backup_sqlite.sh
```

Do not delete `data/vinoth_os.db` when updating the application; that file contains schedules, completion history, and focus history.
