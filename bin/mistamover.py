#!/usr/bin/env python
# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
MiStaMover.py - Script to run MiStaMover Application
===================================================

The ``mistamover.py`` script is run to start the mistamover Application. It is typically installed to initialise when the server starts and is run in daemon mode by the ``lib/daemon.py`` script. However, it can also be run at the command-line.

Usage::

  mistamover.py [<global_config_file>] [oneoff]

If no global config file given, then use ``global.ini`` in ``conf/`` directory, also overriding the variable "top" in section "``[global]``" with the parent directory path.

"""

# Standard library imports
import os
import sys
from optparse import OptionParser

# Set up global variables and paths
this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "bin":
    raise Exception("Must be run from 'bin' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "lib")
debug_on = False
daemon_mode = False

sys.path.append(lib_dir)

# Local imports
import MiStaMoverController
import Daemon

def parseOptions(args):
    return 

def minver():
    print "MiStaMover requires python 2.5 or above"
    sys.exit()

# check that the python interpreter version is at least 2.5
vs = sys.version
vss = vs.split()
vs = vss[0].split('.')
mj = int(vs[0])
mn = int(vs[1])
if mj < 2:
    minver()
if mj == 2 and mn < 5:
    minver()
   
    
# Handle arguments, get configuration
args = sys.argv[1:]

# Handle debug arg first
if "--debug" in args:
    debug_on = True
    args.remove("--debug")

if "--daemon" in args:
    daemon_mode = True
    args.remove("--daemon")

if debug_on and daemon_mode:
    print "Cannot run in daemon and debug modes together. Sorry!"
    sys.exit(1)

if len(args) not in (0, 1, 2):
    print __doc__
    sys.exit(1)

oneoff = False
if len(args) >= 1:
    arg0 = args[0]

    global_config = arg0
    if len(args) == 2:
        if args[1] == "oneoff":
            oneoff = True
else:
    conf_dir = os.path.join(top_dir, "conf")
    global_config = os.path.join(conf_dir, "global.ini")

    os.environ["CONFIG__global__top"] = top_dir

# Set up stager instance an start
sc = MiStaMoverController.MiStaMoverController(global_config, debug_on, oneoff)

# Run as daemon if requested...
if daemon_mode == True:
    dmn = Daemon.DaemonCtl(sc.main, args=[], description="mistamover_controller")
    print "Deamon process 'mistamover' now forked. This process ends."
else:
    sc.main()

