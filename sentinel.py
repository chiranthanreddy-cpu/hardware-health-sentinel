import psutil
import time
import logging
import requests
import wmi
import pythoncom
import socket
import ctypes
import os
import json
from plyer import notification
from datetime import datetime

# --- SECURITY & CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG = {
    "THRESHOLDS": {
        "CPU_PERCENT": 90.0,
        "RAM_PERCENT": 80.0,
        "DISK_PERCENT": 90.0,
        "BATTERY_LOW": 25,
    },
    "TIMEOUTS": {
        "NETWORK": 5,
    },
    "LOG_FILE": os.path.join(BASE_DIR, "health_monitor.log"),
    "STATE_FILE": os.path.join(BASE_DIR, "state.json"),
    "NOTIFICATION_COOLDOWN": 7200  # 2 hours in seconds
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(CONFIG["LOG_FILE"]), logging.StreamHandler()]
)

class SentinelMonitor:
    def __init__(self):
        self.wmi_obj = None
        self.public_ip = "Unknown"
        self.state = self._load_state()

    def _load_state(self):
        """Loads the last known state from a JSON file."""
        if os.path.exists(CONFIG["STATE_FILE"]):
            try:
                with open(CONFIG["STATE_FILE"], "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"notifications": {}, "last_ip": "Unknown"}

    def _save_state(self):
        """Saves the current state to a JSON file."""
        try:
            with open(CONFIG["STATE_FILE"], "w") as f:
                json.dump(self.state, f)
        except Exception as e:
            logging.error(f"Failed to save state: {e}")

    def _should_notify(self, key):
        """Checks if enough time has passed since the last notification for a given key."""
        last_time = self.state["notifications"].get(key, 0)
        if time.time() - last_time > CONFIG["NOTIFICATION_COOLDOWN"]:
            self.state["notifications"][key] = time.time()
            self._save_state()
            return True
        return False

    def _send_notification(self, title, message, key=None):
        """Internal helper to send sanitized notifications with throttling."""
        if key and not self._should_notify(key):
            logging.info(f"Notification suppressed (cooldown): {title}")
            return

        # Sanitize inputs to prevent notification injection (though rare in Windows)
        safe_title = "".join(char for char in title if char.isalnum() or char in " -_")
        logging.warning(f"ALERT: {safe_title} - {message}")
        try:
            notification.notify(
                title=safe_title,
                message=message[:200], # Limit message length
                app_name="Sentinel Monitor",
                timeout=7
            )
        except Exception as e:
            logging.error(f"Notification error: {e}")

    def monitor_resources(self):
        """Checks CPU, RAM, and Disk usage."""
        # CPU
        cpu = psutil.cpu_percent(interval=1)
        if cpu > CONFIG["THRESHOLDS"]["CPU_PERCENT"]:
            top_procs = self._get_top_processes("cpu")
            self._send_notification("High CPU Usage", f"Load: {cpu}%. Top: {top_procs}", key="cpu_high")

        # RAM
        ram = psutil.virtual_memory().percent
        if ram > CONFIG["THRESHOLDS"]["RAM_PERCENT"]:
            top_procs = self._get_top_processes("memory")
            self._send_notification("High RAM Usage", f"Usage: {ram}%. Top: {top_procs}", key="ram_high")

        # DISK
        for part in psutil.disk_partitions():
            if 'fixed' in part.opts:
                usage = psutil.disk_usage(part.mountpoint)
                if usage.percent > CONFIG["THRESHOLDS"]["DISK_PERCENT"]:
                    self._send_notification("Low Disk Space", f"Drive {part.mountpoint} is {usage.percent}% full.", key=f"disk_low_{part.mountpoint}")

        return {"cpu": cpu, "ram": ram}

    def _get_top_processes(self, sort_by="cpu"):
        """Safely retrieves top processes by resource usage."""
        procs = []
        try:
            for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
                try:
                    procs.append(p.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            sort_key = 'cpu_percent' if sort_by == "cpu" else 'memory_percent'
            top = sorted(procs, key=lambda x: x[sort_key] or 0, reverse=True)[:3]
            return ", ".join([f"{p['name']} ({p[sort_key]:.1f}%)" for p in top])
        except Exception:
            return "Unknown"

    def monitor_network(self):
        """Checks latency and public IP stability."""
        # Latency check (Safe socket connection instead of shell ping)
        latency = "Timeout"
        try:
            start = time.time()
            socket.create_connection(("8.8.8.8", 53), timeout=CONFIG["TIMEOUTS"]["NETWORK"])
            latency = f"{(time.time() - start) * 1000:.0f}ms"
        except (socket.timeout, Exception):
            latency = "Offline"

        # IP check (with timeout and error handling)
        new_ip = "Unknown"
        try:
            response = requests.get("https://api.ipify.org", timeout=CONFIG["TIMEOUTS"]["NETWORK"])
            if response.status_code == 200:
                new_ip = response.text.strip()
                # Sanitize IP output
                new_ip = "".join(c for c in new_ip if c.isdigit() or c == '.')
        except Exception:
            new_ip = "Offline"

        # Use stored IP from state for comparison
        stored_ip = self.state.get("last_ip", "Unknown")
        if stored_ip != "Unknown" and new_ip != stored_ip and new_ip != "Offline":
            self._send_notification("Network Change", f"Public IP changed to {new_ip}")
            self.state["last_ip"] = new_ip
            self._save_state()
        elif stored_ip == "Unknown" and new_ip != "Offline":
             # First run or reset
             self.state["last_ip"] = new_ip
             self._save_state()
        
        self.public_ip = new_ip
        return {"latency": latency, "ip": new_ip}

    def monitor_battery(self):
        """Deep battery analytics using WMI."""
        battery = psutil.sensors_battery()
        if not battery:
            return None

        # Basic status
        percent = battery.percent
        plugged = battery.power_plugged
        if percent < CONFIG["THRESHOLDS"]["BATTERY_LOW"] and not plugged:
            self._send_notification("Low Battery", f"Level: {percent}%. Please connect power.", key="battery_low")

        # Deep health (WMI)
        health_info = {}
        try:
            pythoncom.CoInitialize() # Required for WMI in threads/tasks
            w = wmi.WMI(namespace="root\\wmi")
            full_cap = w.ExecQuery("Select FullChargeCapacity from BatteryFullChargedCapacity")[0].FullChargeCapacity
            design_cap = w.ExecQuery("Select DesignCapacity from BatteryStaticData")[0].DesignCapacity
            wear = 100 - (full_cap / design_cap * 100)
            health_info = {"wear": f"{wear:.1f}%", "health_score": f"{100-wear:.1f}%"}
        except Exception:
            health_info = {"wear": "N/A", "health_score": "N/A"}
        finally:
            pythoncom.CoUninitialize()

        return {"percent": percent, "plugged": plugged, "health": health_info}

    def optimize_memory(self):
        """Safely requests Windows to reclaim unused memory from processes."""
        logging.info("Initiating Memory Optimization (Working Set Trim)...")
        count = 0
        
        # Windows API Constants
        # PROCESS_QUERY_INFORMATION (0x0400) | PROCESS_SET_QUOTA (0x0100)
        PROCESS_ACCESS = 0x0400 | 0x0100
        
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # We try to open the process and trim its working set
                    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ACCESS, False, proc.info['pid'])
                    if handle:
                        ctypes.windll.psapi.EmptyWorkingSet(handle)
                        ctypes.windll.kernel32.CloseHandle(handle)
                        count += 1
                except Exception:
                    continue # Skip processes we don't have permission for
            
            logging.info(f"Memory optimization complete. Requested trim on {count} processes.")
        except Exception as e:
            logging.error(f"Memory optimization failed: {e}")

    def run_all(self):
        logging.info("--- Sentinel Diagnostic Cycle Started ---")
        res = self.monitor_resources()
        
        # If RAM is high, trigger optimization
        if res['ram'] > CONFIG["THRESHOLDS"]["RAM_PERCENT"]:
            logging.warning(f"High RAM usage detected ({res['ram']}%). Triggering optimization...")
            self.optimize_memory()
            # Re-check RAM after optimization
            new_ram = psutil.virtual_memory().percent
            logging.info(f"RAM after optimization: {new_ram}%")

        net = self.monitor_network()
        batt = self.monitor_battery()

        logging.info(f"Resources: CPU {res['cpu']}%, RAM {res['ram']}%")
        logging.info(f"Network: Latency {net['latency']}, IP {net['ip']}")
        if batt:
            logging.info(f"Battery: {batt['percent']}% ({'Charging' if batt['plugged'] else 'Discharging'}), Wear: {batt['health']['wear']}")
        
        logging.info("--- Cycle Complete ---")

if __name__ == "__main__":
    monitor = SentinelMonitor()
    monitor.run_all()