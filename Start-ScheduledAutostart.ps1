########################################################################################################################
#
# Start-ScheduledAutostart.ps1
#
# Keep a healthy work-life balance by scheduling your work apps to only start within your working hours and not on your
# days off.
#
# MIT License
# Copyright (c) 2022 biosmanager
#
# GitHub: https://github.com/biosmanager/scheduled-autostart
# Gist: https://gist.github.com/biosmanager/7ad461508f80feb16f02d75619c35b95
#
########################################################################################################################

### Params

param (
    $StartTime = '08:00',
    $EndTime = '17:00',
    $DaysOff = @('Saturday', 'Sunday'),
    $Programs = @('<PATH TO AUTOSTART APPLICATION 1>', '<PATH TO AUTOSTART APPLICATION 1>'),
    [switch]$DelayStart,
    [switch]$ScheduleStop,
    [switch]$ScheduleRestart
)

### Imports

Import-Module PSScheduledJob

### Jobs

$DelayStartJobName = 'ScheduledAutostart-DelayAutostartApplicationsUntilWorkingDay'
$StopJobName = 'ScheduledAutostart-StopAutostartApplicationsAfterEndOfWorkingDay'
$RestartJobName = 'ScheduledAutostart-RestartAutostartApplicationsOnNewWorkingDay'
Unregister-ScheduledJob -Name $DelayStartJobName -Confirm:$False -Force -ErrorAction SilentlyContinue
Unregister-ScheduledJob -Name $StopJobName -Confirm:$False -Force -ErrorAction SilentlyContinue
Unregister-ScheduledJob -Name $RestartJobName -Confirm:$False -Force -ErrorAction SilentlyContinue

### Functions

function Start-AutostartApplications {
    $StartTimeDate = Get-Date $StartTime
    $EndTimeDate = Get-Date $EndTime
    $Date = Get-Date
    
    if ($Date.DayOfWeek -notin $DaysOff -and (($Date.TimeOfDay -ge $StartTimeDate.TimeOfDay) -and ($Date.TimeOfDay -le $EndTimeDate.TimeOfDay))) {
        Write-Output 'Another day, another dollar! Starting autostart applications...'
    
        foreach ($Program in $Programs) {
            Start-Process $Program -RedirectStandardOutput nul
        }

        return $True
    }
    else {
        Write-Output 'Enjoy your freetime :)'

        if ($DelayStart) {
            if (($null -eq $IsWindows) -or $IsWindows) {
                if ($PSVersionTable.PSVersion.Major -le 5) {
                    Write-Output 'Delaying autostart until beginning of next working day...'            
                    $DelayStartTime = Get-Date $StartTime
                    $DelayStartJobTrigger = New-JobTrigger -Daily -At $DelayStartTime
                    Register-ScheduledJob -Name $DelayStartJobName -Trigger $DelayStartJobTrigger -ScriptBlock {
                        if (Start-AutostartApplications) {
                            Unregister-ScheduledJob -Name $DelayStartJobName -Confirm:$False -Force -ErrorAction SilentlyContinue
                        }
                    }
                }
                else {
                    Write-Warning 'Job scheduler only works in Windows PowerShell 5 and below!'
                }
            }
            else {
                Write-Warning 'Job scheduler only works on Windows!'
            }
        }

        return $False
    }
}

function Stop-AutostartApplications {
    $Date = Get-Date
    if ($Date.DayOfWeek -notin $DaysOff -and $Date.TimeOfDay -ge $EndTimeDate.TimeOfDay) {
        foreach ($Program in %Programs) {
            Get-Process | Where-Object { $_.Path -like $Program } | Stop-Process
        }
    }
}

### Script

Start-ScheduledAutostartApplications

if (($null -eq $IsWindows) -or $IsWindows) {
    if ($PSVersionTable.PSVersion.Major -le 5) {
        # Schedule job to reduce work distractions if the computer is still on
        if ($ScheduleStop) {
            Write-Output 'Scheduling stopping of autostart applications...'      
            
            $StopTimeDate = Get-Date $EndTime
            $StopJobTrigger = New-JobTrigger -Daily -At $StopTimeDate
            Register-ScheduledJob -Name $StopJobName -Trigger $StopJobTrigger -ScriptBlock {
                Stop-AutostartApplications
            }
        }
       
        # Restart autostart applications on the next working day if the computer is still on
        if ($ScheduleRestart) {
            Write-Output 'Scheduling restart of autostart applications...'
            
            $RestartTimeDate = Get-Date $StartTime
            $RestartJobTrigger = New-JobTrigger -Daily -At $RestartTimeDate
            Register-ScheduledJob -Name $RestartJobName -Trigger $RestartJobTrigger -ScriptBlock {
                Start-AutostartApplications
            }
        }
    }
    else {
        Write-Warning 'Job scheduler only works in Windows PowerShell 5 and below!'
    }
}
else {
    Write-Warning 'Job scheduler only works on Windows!'
}
