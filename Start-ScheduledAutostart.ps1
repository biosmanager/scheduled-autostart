param (
    $StartTime = '06:00',
    $EndTime = '17:00',
    $DaysOff = @('Saturday', 'Sunday'),
    $Programs = @('C:\Users\biosmanager\AppData\Local\slack\slack.exe', 'C:\Users\biosmanager\AppData\Local\Programs\mattermost-desktop\Mattermost.exe'),
    [switch]$ScheduleStop = $True,
    [switch]$ScheduleRestart = $False
)

Import-Module PSScheduledJob

function Start-AutostartApplications {
    foreach ($Program in $Programs) {
        Start-Process $Program -RedirectStandardOutput nul
    }
}

function Stop-AutostartApplications {
    foreach ($Program in %Programs) {
        Get-Process | Where-Object { $_.Path -like $Program } | Stop-Process
    }
}

function Start-ScheduledAutostartApplications {
    $StartTimeDate = Get-Date $StartTime
    $EndTimeDate = Get-Date $EndTime
    $Date = Get-Date
    
    if ($Date.DayOfWeek -notin $DaysOff -and (($Date.TimeOfDay -ge $StartTimeDate.TimeOfDay) -and ($Date.TimeOfDay -le $EndTimeDate.TimeOfDay))) {
        # Autostart
        Write-Output 'Another day, another dollar!'
    
        Start-AutostartApplications
    }
    else {
        Write-Output 'Enjoy your freetime :)'
    }
}

Start-ScheduledAutostartApplications

if (($null -eq $IsWindows) -or $IsWindows) {
    if ($PSVersionTable.PSVersion.Major -le 5) {
        # Schedule job to reduce work distractions if the computer is still on
        if ($ScheduleStop) {
            $StateChangeTrigger = Get-CimClass `
                -Namespace ROOT\Microsoft\Windows\TaskScheduler `
                -ClassName MSFT_TaskSessionStateChangeTrigger
            $OnUnlockTrigger = New-CimInstance `
                -CimClass $StateChangeTrigger `
                -Property @{
                StateChange = 8  # TASK_SESSION_STATE_CHANGE_TYPE.TASK_SESSION_UNLOCK (taskschd.h)
            } ` -ClientOnly
        
            $StopJobName = 'ScheduledAutostart-StopAutostartApplicationsAfterEndOfWorkingDay'
            Register-ScheduledJob -Name $StopJobName -ScriptBlock {
                $Date = Get-Date
                if ($Date.DayOfWeek -notin $DaysOff -and $Date.TimeOfDay -ge $EndTimeDate.TimeOfDay) {
                    Stop-AutostartApplications
                }
            }

            $Task = Get-ScheduledTask -TaskPath "\Microsoft\Windows\PowerShell\ScheduledJobs\" -TaskName $StopJobName
            $Task | Set-ScheduledTask -Trigger $OnUnlockTrigger
        }
       
        if ($ScheduleRestart) {
            # Restart autostart applications on the next working day if the computer is still on
            $RestartJobName = 'ScheduledAutostart-RestartAutostartApplicationsOnNewWorkingDay'
            $RestartTimeDate = Get-Date $StartTime
            $RestartJobTrigger = New-JobTrigger -Daily -At $RestartTimeDate
            Register-ScheduledJob -Name $RestartJobName -Trigger $RestartJobTrigger -ScriptBlock {
                Start-ScheduledAutostartApplications
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
