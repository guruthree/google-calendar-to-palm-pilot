#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import pisock
import pytz
from ics2csv4pdb import csvHeaders,fetchCalendar

import codecs,os,signal,sys,tempfile
from ConfigParser import ConfigParser
from optparse import OptionParser

# source ~/apps/anaconda3/etc/profile.d/conda.sh 
# conda activate py27

# https://pythonhosted.org/kitchen/unicode-frustrations.html
UTF8Writer = codecs.getwriter('utf8')
sys.systdout = UTF8Writer(sys.stdout)

# https://docs.python.org/2.7/library/signal.html
running = True
def handler(signal_received, frame):
    # Handle any cleanup here
    print('Exiting...')
    running = False
    sys.exit(0)
signal.signal(signal.SIGINT, handler)

# https://docs.python.org/2.7/library/optparse.html
parser = OptionParser()
parser.add_option("-p", "--port", dest="pilotport", help="pilot-link device port, e.g. /dev/ttyUSB0, net:any bt:any", metavar="PORT")
parser.add_option("-c", "--config", dest="configfile", help="ini configuration file with ics URI in [DEFAULT] section", metavar="CONFIGFILE")
(options, args) = parser.parse_args()

if not options.pilotport or not options.configfile:
    parser.print_help()
    exit(1)

# https://docs.python.org/2.7/library/configparser.html
config = ConfigParser({
    'URI': 'https://www.google.com/calendar/ical/en_gb.uk%23holiday%40group.v.calendar.google.com/public/basic.ics',
    'TIMEZONE': 'UTC',
    'FROMYEAR': '2020',
    'ADDALARM': '30',
    'ADDALARM_START': '9',
    'ADDALARM_END': '7'
    })
config.readfp(open(options.configfile))
URI = config.get('DEFAULT', 'URI').split(',')
LOCALTZ = pytz.timezone(config.get('DEFAULT', 'TIMEZONE'))
FROMYEAR = int(config.get('DEFAULT', 'FROMYEAR'))
addalarm = (int(config.get('DEFAULT', 'ADDALARM_START')), int(config.get('DEFAULT', 'ADDALARM_END')), int(config.get('DEFAULT', 'ADDALARM')))

while running:
    print "Waiting for connection on %s..." % options.pilotport
    try:
        # based on pisocktests.py, the pilot-link Python bindings test file
        sd = pisock.pi_socket(pisock.PI_AF_PILOT, pisock.PI_SOCK_STREAM, pisock.PI_PF_DLP)
        pisock.pi_bind(sd, options.pilotport)
        pisock.pi_listen(sd, 1)
        pisock.pi_accept(sd)

        # https://stackoverflow.com/questions/8577137/how-can-i-create-a-tmp-file-in-python/8577225
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as tmp:
                tmp = UTF8Writer(tmp)
                tmp.write(csvHeaders())
                for uri in URI:
                    csv = fetchCalendar(uri, FROMYEAR, LOCALTZ, False, addalarm)
                    tmp.write(csv)
                tmp.close()
                #./pilot-datebook -r csv -f ~/Desktop/pypisock/cal.csv -w pdb -f ~/Desktop/cal.pdb
                pdbfile = "%s.pdb" % path
                cmd = "./pilot-datebook -r csv -f %s -w pdb -f %s" % (path, pdbfile)
                os.system(cmd)

                pisock.dlp_OpenConduit(sd)
                # Python syntax: pi_file_install(sd, cardno, filename, callback)
                print "Sending DatebookDB..."
                pisock.pi_file_install(sd, 0, pdbfile, None)
        finally:
            os.remove(path)
            os.remove(pdbfile)

        pisock.pi_close(sd)
        print "Done"
    finally:
        pass
