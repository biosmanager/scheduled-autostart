import argparse
import asyncio
import easygui
import calendar
import datetime
import os
import dateutil.parser
import schedule
import signal
import subprocess
import time
import psutil
import tkinter as tk
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

parser = argparse.ArgumentParser(description='Keep a healthy work-life balance by scheduling your work apps to only start within your working hours and not on your days off.')
parser.add_argument('--start-time', help='Start time', required=True)
parser.add_argument('--end-time', help='End time', required=True)
parser.add_argument('--days-off', help='Days off', required=False, nargs='*')
parser.add_argument('--programs', help='Programs', required=True, nargs='+')
parser.add_argument('--delay-start', help='Delay start', action='store_true')
parser.add_argument('--schedule-stop', help='Schedule stop', action='store_true')
parser.add_argument('--force-stop', help='Force stop without confirmation', action='store_true')
parser.add_argument('--aggressive-stop', help='Stops all processes that have the same executable name, ignoring if the path matches. Can be useful in some cases when the autostarted program launches other applications, e.g. Slack.', action='store_true')
parser.add_argument('--schedule-restart', help='Schedule start', action='store_true')
parser.add_argument('--calendar-id', help='Calendar ID', required=False)
parser.add_argument('--vacation-keywords', help='Vacation keywords', required=False, nargs='+')
args = parser.parse_args()

first_start = True
start_time = dateutil.parser.parse(args.start_time)
end_time = dateutil.parser.parse(args.end_time)

started_processes = []

def on_vacation_today():
    if args.calendar_id is None or args.vacation_keywords is None:
        return False

    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        today = datetime.datetime.combine(datetime.date.today(), datetime.time()).isoformat() + 'Z'  # 'Z' indicates UTC time
        events_result = service.events().list(calendarId=args.calendar_id, timeMin=today,
                                              maxResults=100, singleEvents=True,
                                              orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            return False

        # Check if all vacation keywords are present in a calendar event
        for event in events:
            if all(keyword.lower() in event['summary'].lower() for keyword in args.vacation_keywords):
                return True

    except HttpError as error:
        print('An error occurred: %s' % error)

def start_programs():
    global first_start
    global started_processes

    date = datetime.datetime.now()
    weekday_str = calendar.day_name[date.weekday()]

    is_vacation = not on_vacation_today()
    is_workday = (args.days_off is None) or (weekday_str not in args.days_off)
    is_withing_working_hours = date.time() > start_time.time() and date.time() < end_time.time()

    if (not is_vacation) and is_workday and is_withing_working_hours:
        print("Another day, another dollar.")

        started_processes = []

        for program in args.programs:
            if psutil.MACOS:
                cmdline = ['open', '-a', program]
            else:
                cmdline = [program]
            print(f"Starting program: {cmdline}")
            started_processes.append(psutil.Popen(cmdline))
        
        return True
    else:
        print("Enjoy your freetime!")

        if (args.delay_start and first_start):
            print("Delaying autostart until beginning of next working day...")
            
            def delay_start_programs():
                if (start_programs()):
                    return schedule.CancelJob

            schedule.every().day.at(args.start_time).do(delay_start_programs)
            first_start = False

        return False


def stop_proc_tree(pid, kill=False, include_parent=True,
                   timeout=None, on_terminate=None):
    """Kill a process tree (including grandchildren) with signal
    "sig" and return a (gone, still_alive) tuple.
    "on_terminate", if specified, is a callback function which is
    called as soon as a child terminates.
    """
    assert pid != os.getpid(), "won't kill myself"
    parent = psutil.Process(pid)
    children = parent.children(recursive=True)
    if include_parent:
        children.append(parent)
    for p in children:
        try:
            if kill:
                p.kill()
            else:
                p.terminate()
        except psutil.NoSuchProcess:
            pass
    gone, alive = psutil.wait_procs(children, timeout=timeout,
                                    callback=on_terminate)
    return (gone, alive)

def stop_programs():
    global started_processes

    print("Stopping scheduled autostart programs...")
    date = datetime.datetime.now()
    weekday_str = calendar.day_name[date.weekday()]

    is_workday = (args.days_off is None) or (weekday_str not in args.days_off)
    is_after_working_hours = date.time() >= end_time.time()

    is_after_working_hours = True

    if is_workday and is_after_working_hours:
        stop = True
        if not args.force_stop:
            msg = 'Do you want to terminate all scheduled autostart applications?\nThis will stop all the following application and its children. Please make sure you have saved all your work before proceeding.\n\n'

            for program in args.programs:
                msg += f"- {program}\n"

            if args.aggressive_stop:
                msg += "\n"
                msg += "This will also kill any applications and its children with the following name:\n\n"
                for program in args.programs:
                    msg += f"- {os.path.basename(program)}\n"

            stop = easygui.ynbox(
                msg, 'Stop scheduled autostart programs?', ('Yes', 'No'))

        if stop:
            for process in started_processes:
                try:
                    _, gone = stop_proc_tree(process.pid)
                    if gone:
                        print(f"Stopped started program and children: {process.exe()}")
                except:
                    pass
            started_processes = []

            if args.aggressive_stop:
                for process in psutil.process_iter():
                    try:
                        for program in args.programs:
                            if os.path.basename(program) in process.exe():
                                _, gone = stop_proc_tree(process.pid, kill=True)
                                if gone:
                                    print(f"Stopped program by image name and children: {process.exe()}")
                    except:
                        pass

start_programs()

if (args.schedule_restart):
    print(f"Scheduling autostart restart every day at {args.start_time}.")
    schedule.every().day.at(start_time.time().strftime("%H:%M")).do(start_programs)

if (args.schedule_stop):
    print(f"Scheduling stop of autostarted programs every day at {args.end_time}.")
    schedule.every().day.at(end_time.time().strftime("%H:%M")).do(stop_programs)
   
while True:
    schedule.run_pending()
    time.sleep(1)