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
from TransferModules.RsyncTransfer import RsyncTransfer
if __name__ == '__main__':
    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--checkVars":
            s = MiStaMoverController.MiStaMoverController("test/conf/rsync_global.ini")
            d = s.dconfigs['rsync']
            r = RsyncTransfer(d)
            r.checkVars()
            r.setFile("testfile")
            print r.setupStopFileCmd()
            print r.setupPushCmd()
        if sys.argv[1] == "--checkVarsFail":
            s = MiStaMoverController.MiStaMoverController("test/conf/rsync_global_fail.ini")
            d = s.dconfigs['rsync']
            r = RsyncTransfer(d)
            try:
                r.checkVars()
                r.setFile("testfile")
                print r.setupStopFileCmd()
            except Exception, ex:
                print "Success - an exception was thrown!\n", str(ex)
