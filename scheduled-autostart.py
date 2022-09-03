import argparse
import calendar
import datetime
import dateutil.parser
import subprocess

parser = argparse.ArgumentParser(description='Keep a healthy work-life balance by scheduling your work apps to only start within your working hours and not on your days off.')
parser.add_argument('--start-time', help='Start time', required=True)
parser.add_argument('--end-time', help='End time', required=True)
parser.add_argument('--days-off', help='Days off', required=False, nargs='*')
parser.add_argument('--programs', help='Programs', required=True, nargs='+')
parser.add_argument('--delay-start', help='Delay start', action='store_true')
parser.add_argument('--schedule-stop', help='Schedule stop', action='store_true')
parser.add_argument('--schedule-restart', help='Schedule start', action='store_true')
args = parser.parse_args('--start-time 09:00 --end-time 17:00 --days-off Sunday --programs slack --delay-start --schedule-stop --schedule-restart'.split())

start_time = dateutil.parser.parse(args.start_time)
end_time = dateutil.parser.parse(args.end_time)
date = datetime.datetime.now()
weekday_str = calendar.day_name[date.weekday()]

if (weekday_str not in args.days_off) and (date.time() > start_time.time()) and (date.time() < end_time.time()):
    print("It's a work day and you're within your working hours.")

    for program in args.programs:
        print(f"Starting program: {program}")
        subprocess.Popen(program, shell=True)

else:
    print("It's not a work day or you're outside your working hours.")