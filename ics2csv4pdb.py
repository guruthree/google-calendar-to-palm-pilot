#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import icalendar
import requests
from datetime import datetime
from datetime import time
from datetime import timedelta # https://docs.python.org/3/library/datetime.html#timedelta-objects
import pytz

# https://github.com/collective/icalendar
# https://icalendar.readthedocs.io/en/latest/usage.html#more-documentation
# https://python-forum.io/thread-2409.html
# https://gist.github.com/meskarune/63600e64df56a607efa211b9a87fb443
# https://gist.github.com/afunTW/bf958eea15835d14aa976990d1f0bb88
# https://stackoverflow.com/questions/3408097/parsing-files-ics-icalendar-using-python

def csvHeaders():
    ALARM_HEADERS = "alarm,advance,advanceUnit"
    REPEAT_HEADERS = "repeatType,repeatForever,repeatEnd,repeatFrequency,repeatDay,repeatWeekdays,repeatWeekstart"
    GENERAL_HEADERS = "untimed,beginDate,beginTime,endDate,endTime,description,note"
    return ','.join([GENERAL_HEADERS, ALARM_HEADERS, REPEAT_HEADERS]) + "\n"

def fetchCalendar(CALURI, FROMYEAR, LOCALTZ, doheaders=True, addalarm=(9,17,30)):
    # return csv formatted ics data for feeding into pilot-datebook
    # CALURI - location of calendar to fetch
    # FROMYEAR - don't export calendar events older than january 1 of this year
    # LOCALTZ - time zone to put dates/times into
    # doheaders - include csv file headers in the returned list
    # addalarm - automatically add an alarm to events to replace the one google doesn't export
    #            tupple of (startrange,endrange,before)
    #            where startrange and endrange are the hours between which to add the alarm
    #            before is the number of minutes before the event to set the alarm for
    #            won't be added to all-day events

    # ics text representation to palm numeric representation
    repeatTypes = {'DAILY':1, 'WEEKLY':2, 'MONTHLY':4, 'YEARLY':5}
    weekdays = {'SU':0, 'MO':1, 'TU':2, 'WE':3, 'TH':4, 'FR':5, 'SA':6}
    weekdaysRepeat = {'SU':1, 'MO':2, 'TU':4, 'WE':8, 'TH':16, 'FR':32, 'SA':64}

    # fetch calendar
    print "Fetching %s..." % CALURI
    calcontents = requests.get(CALURI).text
#    calcontents = requests.get(CALURI, verify=False).text
    cal = icalendar.Calendar.from_ical(calcontents)

    if doheaders == True:
        output = csvHeaders()
    else:
        output = ""

    print "Parsing..."
    for event in cal.walk():
        if event.name == "VEVENT":
            description = event['SUMMARY']
            if 'DESCRIPTION' in event.keys():
                note = event['DESCRIPTION']
                note = note.replace("\r", "")
                note = note.replace("\n", "\\n")
                note = note.replace("\"", "\\\"")
            else:
                note = ""

            dtstart = event.get('DTSTART').dt
            dtend = event.get('DTEND').dt
            
            if isinstance(dtstart, datetime):
                # https://stackoverflow.com/questions/1111317/how-do-i-print-a-datetime-in-the-local-timezone/54837528
                dtstart2 = dtstart.astimezone(LOCALTZ)
                dtend2 = dtend.astimezone(LOCALTZ)
                untimed = 0
                beginDate = dtstart2.date()
                beginTime = dtstart2.time()
                endDate = dtend2.date()
                endTime = dtend2.time()
                if dtstart > pytz.UTC.localize(datetime(FROMYEAR, 1, 1)):
                    recent = 1
                else:   
                    recent = 0
            else:
                # all day event so no timezone info
                untimed = 1
                beginDate = dtstart
                beginTime = time(0)
                endDate = dtend
                endTime = time(0)
                if dtstart > datetime(FROMYEAR, 1, 1).date():
                    recent = 1
                else:
                    recent = 0

            alarm = 0
            advance = 0
            advanceUnit = 0
            alarmTime = timedelta(99999)
            for analarm in event.walk():
                if analarm.name == "VALARM":
                    alarm = 1
                    alarmTimeT = -analarm['TRIGGER'].dt
                    if alarmTimeT < alarmTime:
                        alarmTime = alarmTimeT;
            if alarm == 0 and addalarm != None and addalarm[2] != 0:
                if beginTime > time(addalarm[0]) and endTime < time(addalarm[1]):
                    alarmTime = timedelta(seconds=addalarm[2]*60)
                    alarm = 1
                
            if alarm:
                alarmMinutes = alarmTime.days*1440 + alarmTime.seconds/60
                if alarmMinutes % 1440 == 0:
                    advance = alarmMinutes // 1440
                    advanceUnit = 2
                elif alarmMinutes % 60 == 0:
                    advance = alarmMinutes // 60
                    advanceUnit = 1
                else:
                    advance = alarmMinutes
                    advanceUnit = 0

            repeatType = 0
            repeatForever = 0
            repeatEnd = ''
            repeatFrequency = 0
            repeatDay = 0
            repeatWeekdays = 0
            repeatWeekstart = 0
            if 'RRULE' in event.keys():            
                if 'UNTIL' in event['RRULE'].keys():                
                    repeatEnd = event['RRULE']['UNTIL'][0]
                    if isinstance(repeatEnd, datetime):
                        repeatEnd = repeatEnd.astimezone(LOCALTZ)
                        if repeatEnd > pytz.UTC.localize(datetime(FROMYEAR, 1, 1)):
                            recent = 1
                        repeatEnd = str(repeatEnd.date()) + " " + str(repeatEnd.time())
                    else:
                        if repeatEnd > datetime(FROMYEAR, 1, 1).date():
                            recent = 1
                        repeatEnd = str(repeatEnd) + " 00:00:00"
                else:
                    repeatForever = 1

                repeatType = repeatTypes[event['RRULE']['FREQ'][0]]
                if 'INTERVAL' in event['RRULE'].keys():
                    repeatFrequency = event['RRULE']['INTERVAL'][0]
                else:
                    repeatFrequency = 1

                if repeatType == 5: # yearly
                    pass

                elif repeatType == 4: # monthly (day of the month)
                    if 'BYMONTHDAY' in event['RRULE'].keys():
                        repeatDay = event['RRULE']['BYMONTHDAY'][0] - 1
                    elif 'BYDAY' in event['RRULE'].keys():
                        repeatType = 3 # monthly (day of week of month, e.g. 1st tuesday, '1TU')
                        repeatDay = (int(event['RRULE']['BYDAY'][0][0])-1) * 7 + weekdays[event['RRULE']['BYDAY'][0][1:3]]

                elif repeatType == 1: # daily
                    if 'COUNT' in event['RRULE'].keys():
                        repeatEnd = dtend + (event['RRULE']['COUNT'][0] - 1) * timedelta(days=1)
                        if isinstance(repeatEnd, datetime):
                            repeatEnd = repeatEnd.astimezone(LOCALTZ)
                            if repeatEnd > pytz.UTC.localize(datetime(FROMYEAR, 1, 1)):
                                recent = 1
                            repeatEnd = str(repeatEnd.date()) + " " + str(repeatEnd.time())
                        else:
                            if repeatEnd > datetime(FROMYEAR, 1, 1).date():
                                recent = 1
                            repeatEnd = str(repeatEnd) + " 00:00:00"
                        repeatForever = 0

                elif repeatType == 2: # weekly
                    if 'WKST' in event['RRULE'].keys():
                        repeatWeekstart = weekdays[event['RRULE']['WKST'][0]]

                    if 'COUNT' in event['RRULE'].keys() and not 'UNTIL' in event['RRULE'].keys():
                        repeatEnd = dtend + (event['RRULE']['COUNT'][0] - 1) * timedelta(days=7)
                        if isinstance(repeatEnd, datetime):
                            repeatEnd = repeatEnd.astimezone(LOCALTZ)
                            repeatEnd = str(repeatEnd.date()) + " " + str(repeatEnd.time())
                        else:
                            repeatEnd = str(repeatEnd) + " 00:00:00"
                        repeatForever = 0

                    if 'BYDAY' in event['RRULE'].keys():
                        for day in event['RRULE']['BYDAY']:
                            repeatWeekdays = repeatWeekdays + weekdaysRepeat[day]


            if repeatForever == 1 or recent:
                line = "%i,%s,%s,%s,%s,\"%s\",\"%s\",%i,%i,%i,%i,%i,%s,%i,%i,%i,%i\n" % \
                    (untimed, beginDate, beginTime, endDate, endTime, description, note, alarm, advance, advanceUnit, \
                     repeatType,repeatForever,repeatEnd,repeatFrequency,repeatDay,repeatWeekdays,repeatWeekstart)
                output += line

    print "Done parseing"

    return output
