# Scheduled autostart

Keep a healthy work-life balance by scheduling your work apps to only start within your working hours and not on your days off. 

## Features

- Start autostart applications only within working hours.
- Define days off where to you don't want your autostart apps to launch.
- (Optional) Delay autostart to the beginning of your working day (e.g. if you start your computer before work).
- (Optional) Stop work apps after your working hours (triggers at desktop unlock).
- (Optional) Restart work apps on the next work day (e.g. if you leave your computer on at night). 

### Planned features

- Sync with Google Calendar to respect your vacations.
- macOS support (scheduled jobs require Windows PowerShell 5 or lower)

## Usage

Create a task in Windows task scheduler, triggering at logon, running with highest privileges (necessary to create scheduled jobs).