# Hardware Health Sentinel - Task Scheduler Setup (Universal Version)
$ScriptName = "sentinel.py"
$CurrentDir = "C:\Users\chiru\hardware-health-sentinel"
$PythonPath = (Get-Command pythonw).Source
$TaskName = "HardwareHealthSentinel"

# 1. Define the action
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$CurrentDir\$ScriptName`"" -WorkingDirectory $CurrentDir

# 2. Define the trigger (Starts now and repeats every 30 minutes indefinitely)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)

# 3. Define settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$true -DontStopIfGoingOnBatteries:$false -StartWhenAvailable:$true

# 4. Register the task (Force overwrite)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Monitors hardware health (battery/cpu) every 30 minutes." -Force

Write-Host "Task '$TaskName' has been updated and scheduled successfully!" -ForegroundColor Green
Write-Host "It is now set to run every 30 minutes starting immediately."
