# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import sys
import os

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "test":
    raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)


import MiStaMoverController

if __name__ == '__main__':
    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--dump":
            s = MiStaMoverController.MiStaMoverController("test/conf/rsync_global.ini")
            s.dumpConfig()
        if sys.argv[1] == "--read":
            s = MiStaMoverController.MiStaMoverController("test/conf/rsync_global.ini")
            s.readConfig("test/conf/rsync_global.ini")
        if sys.argv[1] == "--readFail":
            print "should output :-"
            print "unable to access global.config_dir /home/users/jhorton/Download/SVN/jah/mistamover/test/conf2"
            s = MiStaMoverController.MiStaMoverController("test/conf/rsync_global_fail2.ini")
            s.readConfig("test/conf/rsync_global_fail2.ini")
