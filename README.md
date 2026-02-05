# Hardware Health Sentinel

A lightweight Python background monitor that keeps an eye on your system's vital signs and alerts you to potential issues.

## Advanced Features (v2.0)
- **Resource Detective**: Identifies top 3 processes causing high CPU/RAM usage.
- **Disk Pulse**: Monitors all disk partitions for low space.
- **Network Stability**: Tracks connection latency and public IP changes.
- **Battery Deep-Health**: Calculates battery wear levels using Windows WMI.
- **Modular Design**: Built with object-oriented principles for easy expansion.

## Security Measures
- **Input Sanitization**: All system-retrieved strings are sanitized before logging/notifying.
- **Safe Network Calls**: Uses socket-level checks and strict timeouts (5s) to prevent hangs.
- **Non-Privileged**: Operates without requiring shell execution (`os.system`), reducing injection risks.
- **No Dangerous Functions**: Strict avoidance of `eval()` or `exec()`.

## Installation
Requires `psutil`, `plyer`, `requests`, `wmi`, and `pywin32`:
```bash
pip install psutil plyer requests wmi pywin32
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
