# Windows System Sentinel - Task Scheduler Setup
$ScriptName = "sentinel.py"
$CurrentDir = "C:\Users\chiru\hardware-health-sentinel"
$PythonPath = (Get-Command python).Source
$TaskName = "HardwareHealthSentinel"
$ActionExecutable = $PythonPath
$ActionArguments = "`"$CurrentDir\$ScriptName`""

# Create the action
$Action = New-ScheduledTaskAction -Execute $ActionExecutable -Argument $ActionArguments

# Create the trigger (At startup and repeat every 30 minutes)
$Trigger = New-ScheduledTaskTrigger -AtLogOn -Once
$Trigger.Repetition = (New-ScheduledTaskRepetitionSet -Interval (New-TimeSpan -Minutes 30) -StopAtDurationEnd $false)

# Create the settings
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries:$true -DontStopIfGoingOnBatteries:$false

# Register the task
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Monitors hardware health (battery/cpu) every 30 minutes." -Force

Write-Host "Task '$TaskName' has been scheduled successfully!" -ForegroundColor Green
Write-Host "It will run every 30 minutes while logged in."
