# google-calendar-to-palm-pilot
Make your Palm Pilot useful again by downloading your Google Calendar to it.

`senddatebook.py`, when running, should listen on the specified port and upon triggering a HotSync on the PalmOS device connected to that port, fetch a specified set of Google Calendar/ics files, convert these, and send them to the PalmOS device.

Requires [pilot-link](https://github.com/jichu4n/pilot-link), [pilot-datebook](https://github.com/guruthree/pilot-datebook), and the python [iCalendar](https://github.com/collective/icalendar) library. Also, sorry, Python 2.7. Only tested under Linux.

No warranty or guarantee is offered or implied. Some calendar events may not show up, repeat correctly, or may not have an alarm. Times may be off with respect to daylight savings times. Soooo much of this is untested.

## Setup
1. Install pilot-link and pilot-datebook
2. If you don't already have a Python 2.7 environment with the iCalendar Python library, install [Anaconda](https://www.anaconda.com/products/individual) to get one
    1. After installing Anaconda either run `conda init` or source the profile, e.g. `source ~/anaconda3/etc/profile.d/conda.sh`
    2. Setup a Python 2.7 environment `conda create -n py27 python=2.7`
    3. Install the iCalendar python library `conda install icalendar`
    4. Activate and do everything else inside the Python 2.7 environemnt `conda activate py27`
3. Setup the pilot-link Python 2.7 bindings (I couldn't get these working in Python 3 or I would have used it)
    1. Change to the pilot-link Python bindings folder, e.g. `cd pilot-link-0.2.12.5/bindings/Python`
    2. Build the bindings `python2 setup.py build`
4. Download this repo, e.g. `git clone https://github.com/guruthree/google-calendar-to-palm-pilot.git`
5. Get some files into `google-calendar-to-palm-pilot`
    1. Copy `_pisock.so`, `pisock.py`, and `pisockextras.py` from the `pilot-link-0.2.12.5/bindings/Python/build/lib.linux-x86_64-2.7`
    2. Add a link to the compiled `pilot-datebook` binary
6. Edit `datebook.cfg` to point to your calendar ics files, which for Google calendar [can be found in calendar settings](https://support.google.com/calendar/answer/37648?hl=en#zippy=%2Cget-your-calendar-view-only)
    1. Multiple calendars can be specified by comma separation
    2. The PalmOS devices local time zone can be specified in the config file
    3. Calendar entries from before the January 1st of the specified year will be ignored
7. Run `senddatebook.py` with the port the PalmOS device is connected to specified via `-p` and the configuration file specified via `-c`, e.g. `./senddatebook.py -p net:any -c datebook.cfg`

## Expected behaivour
Output should be something like this:
```
$ ./senddatebook.py -p net:any -c datebook.cfg
Waiting for connection on net:any...
Fetching https://www.google.com/calendar/ical/en_gb.uk%23holiday%40group.v.calendar.google.com/public/basic.ics...
Parsing...
Done parseing
                                                  
Statistics:
Input file </tmp/tmpdnA6us>, format <csv>:
Input file format <untimed,beginDate,beginTime,endDate,endTime,description,note,alarm,advance,advanceUnit,repeatType,repeatForever,repeatEnd,repeatFrequency,repeatDay,repeatWeekdays,repeatWeekstart>
Input file header <untimed,beginDate,beginTime,endDate,endTime,description,note,alarm,advance,advanceUnit,repeatType,repeatForever,repeatEnd,repeatFrequency,repeatDay,repeatWeekdays,repeatWeekstart>
Lines read: 76
Records read: 75
Csv field <untimed> was read 75 times
Csv field <beginDate> was read 75 times
Csv field <beginTime> was read 75 times
Csv field <endDate> was read 75 times
Csv field <endTime> was read 75 times
Csv field <description> was read 75 times
Csv field <note> was read 75 times
Csv field <alarm> was read 75 times
Csv field <advance> was read 75 times
Csv field <advanceUnit> was read 75 times
Csv field <repeatType> was read 75 times
Csv field <repeatForever> was read 75 times
Csv field <repeatEnd> was read 75 times
Csv field <repeatFrequency> was read 75 times
Csv field <repeatDay> was read 75 times
Csv field <repeatWeekdays> was read 75 times
Csv field <repeatWeekstart> was read 75 times

Output file </tmp/tmpdnA6us.pdb>, format <pdb>:
Records written: 75

Sending DatebookDB...
Done
Waiting for connection on net:any...
```

The script should just loop for ever, but quit gracefully on Ctrl-C. The default configuration will load in UK national holidays.

![Summer Bank Holiday (regional holiday)](screenshot.jpg)
