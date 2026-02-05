import psutil
import time
import logging
import os
from plyer import notification
from datetime import datetime

# Setup logging
LOG_FILE = "health_monitor.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def send_alert(title, message):
    logging.warning(f"ALERT: {title} - {message}")
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Sentinel Health Monitor",
            timeout=10
        )
    except Exception as e:
        logging.error(f"Failed to send notification: {e}")

def check_battery():
    battery = psutil.sensors_battery()
    if battery is None:
        return # No battery detected (e.g., Desktop PC)
    
    percent = battery.percent
    power_plugged = battery.power_plugged
    
    # Alert if battery < 25% and not charging
    if percent < 25 and not power_plugged:
        send_alert("Low Battery Warning", f"Battery is at {percent}%. Please plug in your charger.")
    
    return percent, power_plugged

def check_cpu():
    cpu_usage = psutil.cpu_percent(interval=1)
    
    # Alert if CPU usage is very high
    if cpu_usage > 90:
        send_alert("High CPU Usage", f"System is under heavy load: {cpu_usage}% usage.")
    
    return cpu_usage

def main():
    logging.info("--- Hardware Health Sentinel Started ---")
    
    # In a scheduled/service context, we might run this once or in a loop
    # For a "QoL" upgrade, checking every 5 minutes is efficient
    try:
        batt_status = check_battery()
        cpu_status = check_cpu()
        
        if batt_status:
            percent, plugged = batt_status
            status = "Charging" if plugged else "Discharging"
            logging.info(f"Status: Battery {percent}% ({status}), CPU {cpu_status}%")
        else:
            logging.info(f"Status: CPU {cpu_status}% (No battery detected)")
            
    except Exception as e:
        logging.error(f"Error during health check: {e}")

if __name__ == "__main__":
    main()
