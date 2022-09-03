import argparse
import calendar
import datetime
import dateutil.parser
import schedule
import subprocess
import time
import psutil

parser = argparse.ArgumentParser(description='Keep a healthy work-life balance by scheduling your work apps to only start within your working hours and not on your days off.')
parser.add_argument('--start-time', help='Start time', required=True)
parser.add_argument('--end-time', help='End time', required=True)
parser.add_argument('--days-off', help='Days off', required=False, nargs='*')
parser.add_argument('--programs', help='Programs', required=True, nargs='+')
parser.add_argument('--delay-start', help='Delay start', action='store_true')
parser.add_argument('--schedule-stop', help='Schedule stop', action='store_true')
parser.add_argument('--schedule-restart', help='Schedule start', action='store_true')
args = parser.parse_args()

first_start = True
start_time = dateutil.parser.parse(args.start_time)
end_time = dateutil.parser.parse(args.end_time)

def start_programs():
    date = datetime.datetime.now()
    weekday_str = calendar.day_name[date.weekday()]

    if (weekday_str not in args.days_off) and (date.time() > start_time.time()) and (date.time() < end_time.time()):
        print("Another day, another dollar.")

        for program in args.programs:
            if psutil.MACOS:
                cmdline = ['open', '-a', program]
            else:
                cmdline = [program]
            print(f"Starting program: {cmdline}")
            subprocess.Popen(cmdline)
        
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

def stop_programs():
    print("Stopping scheduled autostart programs...")
    date = datetime.datetime.now()
    weekday_str = calendar.day_name[date.weekday()]
    if (weekday_str not in args.days_off) and (date.time() >= start_time.time()):
        for program in args.programs:
            processes = [p for p in psutil.process_iter() if p.exe() == program]
            for process in processes:
                process.kill()

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