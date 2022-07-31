param (
    $StartTime = '09:00',
    $EndTime = '18:00',
    $DaysOff = @('Saturday', 'Sunday')
)

$StartTimeDate = Get-Date $StartTime
$EndTimeDate = Get-Date $EndTime
$Date = Get-Date

if ($Date.DayOfWeek -notin $DaysOff -and (($Date.TimeOfDay -ge $StartTimeDate.TimeOfDay) -and ($Date.TimeOfDay -le $EndTimeDate.TimeOfDay))) {
    # Autostart
    Write-Output 'Another day, another dollar!'

    Start-Process '<program1>' -RedirectStandardOutput nul
    Start-Process '<program2>' -RedirectStandardOutput nul
}
else {
    Write-Output 'Enjoy your freetime :)'
}
