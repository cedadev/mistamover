# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import sys
import os
import time

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "test":
    raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)


import StagerController
import AlertEmailer
if __name__ == '__main__':
    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--runLog":
            s = StagerController.StagerController("test/email_global.ini")
            s.startLogServer()
            s.checkConfig()
            s.info("info test message")
            s.critical("critical test message")
            s.info("info test message")
            print "sleeping"
            time.sleep(20)
            s.stopLogServer()
