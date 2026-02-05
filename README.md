# Hardware Health Sentinel

A lightweight Python background monitor that keeps an eye on your system's vital signs and alerts you to potential issues.

## Features
- **Battery Monitoring**: Alerts you if the battery drops below 25% while not charging.
- **CPU Monitoring**: Alerts you if CPU usage exceeds 90%.
- **Logging**: Maintains a history of system status in `health_monitor.log`.
- **Desktop Notifications**: Uses native Windows notifications for urgent alerts.

## Installation
Requires `psutil` and `plyer`:
```bash
pip install psutil plyer
```

## Usage
Run once:
```bash
python sentinel.py
```

## Auto-Scheduling
To have this run in the background every 30 minutes:
1. Open PowerShell as Administrator.
2. Run the setup script:
   ```powershell
   ./schedule_sentinel.ps1
   ```
