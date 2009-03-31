#!/usr/bin/env python

__version__ = "$Revision$"
__date__ = "$Date$"
__prog__ = "fup_triggers"
__Id__ = "$Id$"
__title__ = "triggers versus time"

import sys, os
from optparse import *

from glue import lal
from pylal import followup_trigger

##############################################################################
#
#  MAIN PROGRAM
#
##############################################################################
usage = """ %prog [options]
"""

parser = OptionParser( usage )

parser.add_option("-v","--version",action="store_true",default=False,\
    help="display version information and exit")

parser.add_option("","--verbose",action="store_true",\
    default=False,help="print information" )

parser.add_option("","--followup-exttrig",action="store_true",\
    default=False,help="set the exttrig flag for followup" )

parser.add_option("-P","--output-path",action="store",\
    type="string",default="",  metavar="PATH",\
    help="path where the figures would be stored")

parser.add_option("-O","--enable-output",action="store_true",\
    default="false",  metavar="OUTPUT",\
    help="enable the generation of the html and cache documents")

parser.add_option("", "--figure-resolution",action="store",type="int",\
    default=50, metavar="resolution of the thumbnails (50 by default)", \
    help="resolution to be used when creating thumbnails")

parser.add_option("-u","--user-tag",action="store",type="string",\
    default="", metavar=" USERTAG",\
    help="The user tag used in the name of the figures" )

parser.add_option("-i","--event-id",action="store",type="string",\
    default=None, metavar=" STRING",\
    help="The event id used in the name of the figures")

parser.add_option("-c","--cache-file",action="store",type="string",\
    default=None, metavar=" PATH",\
    help="specify cache file to be read as input (must contain all xml files)")

parser.add_option("-g","--gps-time",action="store",type="float",\
    default=None, metavar=" PATH",\
    help="gps time at which the plots should be made")

parser.add_option("-w","--windows",action="store",type="string",\
    default=None, metavar=" STRING",\
    help="provide list of window sizes to make the plots.\
    Window sizes must be separated by comas. Ex: \"20,300\"")

parser.add_option("","--ifo-times",action="store",\
    type="string", default=None, metavar=" IFO_TIMES",\
    help="provide ifo_times for naming figures")

parser.add_option("","--followup-sned",action="store",\
    type="string", default=None, metavar=" PATH",\
    help="specify path to the sned-executable, use for spinning injections")

parser.add_option("","--followup-tag",action="store",\
    type="string", default=None, metavar=" STRING",\
    help="select an injection run using tag")

command_line = sys.argv[1:]
(opts,args) = parser.parse_args()


#################################
# if --version flagged
if opts.version:
  print "$Id$"
  sys.exit(0)

#################################

opts.output_path = opts.output_path +'/'

# create output file if required
if not os.path.exists( opts.output_path ):
  os.mkdir (opts.output_path)

if not os.path.exists( opts.output_path+"Images" ):
  os.mkdir (opts.output_path+"Images")


opts.prefix = opts.ifo_times + "-" + __prog__ + "_" + opts.event_id
cache = lal.Cache.fromfile(open(opts.cache_file))

windowList = opts.windows.split(",")

for win in windowList:
  opts.suffix = "-window" + str(win)
  opts.followup_time_window = float(win)
  followup = followup_trigger.FollowupTrigger(cache, opts, False)
  followup.from_time(opts.gps_time)

