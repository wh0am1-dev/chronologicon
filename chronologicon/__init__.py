# -*- coding: utf-8 -*-

# Chronologicon v4.x
# Rutherford Craze
# https://craze.co.uk
# 181028

import os
import time
import json
from easysettings import EasySettings


LOGS_FILENAME = 'logs.json'
STATS_FILENAME = 'stat.json'
PRESAVE_FILENAME = 'temp.json'

LOGS_DEFAULT = []

CUR_FILEPATH = os.path.dirname(__file__)
CUR_LOG = {
    'TIME_START': 0,
    'TIME_END': 0,
    'TIME_LENGTH': 0,
    'DISC': "",
    'PROJ': "",
    'XNOTE': ""
}
CUR_STATS = {
    'discbytime': {},
    'projbytime': {},
    'projbydisc': {},
    'workbyhour': {},
    'avgloglength': 0,
    'totallogs': 0,
    'totaltime': 0
}

PREFS = EasySettings(os.path.join(CUR_FILEPATH, 'prefs.conf'))


# --CORE-FUNCTIONS----------------------------------

def Preflights():  # Check any mission-critical files and create missing ones.
    global PREFS

    # Check save directory
    if PREFS.has_option('SAVE_DIR'):
        if os.path.isdir(PREFS.get('SAVE_DIR')):
            pass
        else:
            print("Save directory couldn't be verified. Please use the '$ chron directory' command to set a new one.")
            return False
    else:
        print("No save directory specified. Please use the '$ chron directory' command to set one.")
        return False

    # Check logs file
    if os.path.exists(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME)):
        pass
    else:
        print("Creating logs file...")
        try:
            # os.makedirs(os.path.dirname(LOGS_FILENAME), exist_ok=True)
            with open(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME), "w") as LOGS_FILE:
                LOGS_FILE.write(json.dumps(LOGS_DEFAULT))
        except Exception as e:
            print("Unable to create log file. Please check your install.\nError: " + str(e))
            return False

    # Check stats file
    if os.path.exists(os.path.join(PREFS.get('SAVE_DIR'), STATS_FILENAME)):
        pass
    else:
        print("Creating stats file...")
        try:
            # os.makedirs(os.path.dirname(LOGS_FILENAME), exist_ok=True)
            with open(os.path.join(PREFS.get('SAVE_DIR'), STATS_FILENAME), "w") as STATS_FILE:
                pass
        except Exception as e:
            print("Unable to create stats file. Please check your install.\nError: " + str(e))
            return False

    # Check temp file
    if os.path.exists(os.path.join(CUR_FILEPATH, PRESAVE_FILENAME)):
        pass
    else:
        print("Creating temporary save file...")
        try:
            with open(os.path.join(CUR_FILEPATH, PRESAVE_FILENAME), "w") as PRESAVE_FILE:
                pass
        except Exception as e:
            print("Unable to create temporary save file. Please check your install.\nError: " + str(e))
            return False

    return True


def ChangeSaveDir(newSaveDir):
    global PREFS
    PREFS.setsave('SAVE_DIR', os.path.expanduser(newSaveDir))
    print("Save directory updated.")


# Start a new log and save its initial parameters to the presave file
def StartLog(args):
    if len(args) < 2:
        print("Not enough information to start a new log.\nUsage: '$ chron -s <discipline> <project> <optional_note>'")
    else:
        try:
            # Abort if there's already a log running
            if os.path.getsize(os.path.join(CUR_FILEPATH, PRESAVE_FILENAME)) > 10:
                print("Log already in progress.")
                return
        except Exception as e:
            print("Error checking extant temp file. If this is your first log, please ignore this message.")

        CUR_LOG['TIME_START'] = int(time.time() * 1000)
        CUR_LOG['DISC'] = args[0]
        CUR_LOG['PROJ'] = args[1]
        if len(args) > 2:
            CUR_LOG['XNOTE'] = args[2]

        try:
            with open(os.path.join(CUR_FILEPATH, PRESAVE_FILENAME), 'w+') as PRESAVE_FILE:
                PRESAVE_FILE.write(json.dumps(CUR_LOG))
        except Exception as e:
            print("Unable to start log.\nError: " + str(e))
            return

        print("Started new log with discipline '" + CUR_LOG['DISC'] + "' and project '" + CUR_LOG['PROJ'] + "'.")


# Cancel an in-progress log and reset the presave file
def CancelLog(quietly=False):
    try:
        with open(os.path.join(CUR_FILEPATH, PRESAVE_FILENAME), 'w') as PRESAVE_FILE:
            PRESAVE_FILE.write("")
    except Exception as e:
        print("Error ending previous log:\n" + str(e))
        return

    if not quietly:
        print("Log cancelled.")


# Display any current logs
def Status():
    try:
        with open(os.path.join(CUR_FILEPATH, PRESAVE_FILENAME)) as PRESAVE_FILE:
            CUR_LOG = json.load(PRESAVE_FILE)
            print("Log in progress with discipline '" + CUR_LOG['DISC'] + "' and project '" + CUR_LOG['PROJ'] + "'.")
    except Exception as e:
        print("No log in progress.")
        return


# Record the current log and clear the presave file
def StopLog():
    try:
        with open(os.path.join(CUR_FILEPATH, PRESAVE_FILENAME)) as PRESAVE_FILE:
            CUR_LOG = json.load(PRESAVE_FILE)
    except Exception as e:
        print("No log in progress.")
        return

    CUR_LOG['TIME_END'] = int(time.time() * 1000)
    CUR_LOG['TIME_LENGTH'] = (CUR_LOG['TIME_END'] - CUR_LOG['TIME_START']) // 1000
    seconds = str(CUR_LOG['TIME_LENGTH'])

    try:
        with open(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME), 'rb+') as LOGS_FILE:
            LOGS_FILE.seek(-1, os.SEEK_END)
            LOGS_FILE.truncate()

        with open(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME), 'a') as LOGS_FILE:
            if os.path.getsize(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME)) > 10:
                LOGS_FILE.write(',')
            LOGS_FILE.write('\n' + json.dumps(CUR_LOG, indent=4) + ']')

        CancelLog(True)

        if seconds == '1':
            print("Log complete. Tracked " + seconds + " second.")
        else:
            print("Log complete. Tracked " + seconds + " seconds.")

        SaveStats()

    except Exception as e:
        print("Unable to save log. Please try again or check your install.\nError: " + str(e))


# Create/ overwrite stats file with info from all logs
def SaveStats():
    try:
        # Read/ generate stats from logs file
        with open(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME)) as LOGS_FILE:
            LOGS = json.load(LOGS_FILE)
            for log in range(len(LOGS)):
                thisLog = LOGS[log]

                # Total logs
                CUR_STATS['totallogs'] = len(LOGS)

                # Total ms tracked
                CUR_STATS['totaltime'] += thisLog['TIME_LENGTH']

                # Average log duration
                CUR_STATS['avgloglength'] = CUR_STATS['totaltime'] // CUR_STATS['totallogs']

                # Disciplines by time
                CUR_STATS['discbytime'][thisLog['DISC']] = CUR_STATS['discbytime'].get(thisLog['DISC'], 0) + thisLog['TIME_LENGTH']

                # Projects by time
                CUR_STATS['projbytime'][thisLog['PROJ']] = CUR_STATS['projbytime'].get(thisLog['PROJ'], 0) + thisLog['TIME_LENGTH']

                # Projects-by-discipline breakdown assignment
                CUR_STATS['projbydisc'][thisLog['PROJ']] = CUR_STATS['projbydisc'].get(thisLog['PROJ'], dict())
                CUR_STATS['projbydisc'][thisLog['PROJ']][thisLog['DISC']] = CUR_STATS['projbydisc'][thisLog['PROJ']].get(thisLog['DISC'], 0) + thisLog['TIME_LENGTH']

                # Productivity by hour
                if thisLog['TIME_LENGTH'] < 3601:  # Simple entry for single-hour logs
                    logHour = time.strftime("%H", time.localtime(thisLog['TIME_START'] / 1000))
                    CUR_STATS['workbyhour'][logHour] = CUR_STATS['workbyhour'].get(logHour, 0) + 1
                else:
                    for h in range((thisLog['TIME_LENGTH'] // 3600) + 1):  # For multi-hour logs, log all hours covered
                        logHour = time.strftime("%H", time.localtime((thisLog['TIME_START'] + (3600000 * h)) / 1000))
                        CUR_STATS['workbyhour'][logHour] = CUR_STATS['workbyhour'].get(logHour, 0) + 1

        # Write statistics to stats file
        with open(os.path.join(PREFS.get('SAVE_DIR'), STATS_FILENAME), 'w') as STATS_FILE:
            STATS_FILE.write('[' + json.dumps(CUR_STATS, indent=4).lower() + ']')
    except Exception as e:
        print("Unable to update statistics file.\nError: " + str(e))


def LoadStats():
    try:
        # Load statistics from stats file
        with open(os.path.join(PREFS.get('SAVE_DIR'), STATS_FILENAME), 'r') as STATS_FILE:
            CUR_STATS = json.load(STATS_FILE)
            return CUR_STATS
    except Exception as e:
        return False


def LoadLogs():  # Used by maintenance
    try:
        # Load logs from logs file
        with open(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME), 'r') as LOGS_FILE:
            CUR_LOGS = json.load(LOGS_FILE)
            return CUR_LOGS
    except Exception as e:
        return False


def Backup():
    try:
        with open(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME)) as LOGS_FILE:
            with open(os.path.join(PREFS.get('SAVE_DIR'), 'chron_backup-' + time.strftime("%y%m%d_%H%M", time.localtime()) + '.json'), 'w') as BACKUP_FILE:
                BACKUP_FILE.write(LOGS_FILE.read())
        print("Log file backed up.")
    except Exception as e:
        print("Unable to back up logs.\nError: " + str(e))


def Export(location):
    try:
        with open(os.path.join(PREFS.get('SAVE_DIR'), LOGS_FILENAME)) as LOGS_FILE:
            with open(os.path.join(location, 'chron-data-' + time.strftime("%y%m%d_%H%M", time.localtime()) + '.json'), 'w') as EXPORT_FILE:
                EXPORT_FILE.write(LOGS_FILE.read())
        print("Data file exported.")
    except Exception as e:
        print("Unable to export data.\nError: " + str(e))

    try:
        with open(os.path.join(PREFS.get('SAVE_DIR'), STATS_FILENAME)) as STATS_FILE:
            with open(os.path.join(location, 'chron-stat-' + time.strftime("%y%m%d_%H%M", time.localtime()) + '.json'), 'w') as EXPORT_FILE:
                EXPORT_FILE.write(STATS_FILE.read())
        print("Stats file exported.")
    except Exception as e:
        print("Unable to export stats.\nError: " + str(e))
