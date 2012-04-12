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

from TransferModules.TransferBase import TransferBase
#from LoggerClient import LoggerClient
import StagerController

if __name__ == '__main__':
    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--runPipe":
            s = StagerController.StagerController("test/conf/rsync_global.ini")
            t = TransferBase()
            t.setConfig(s.gconfig)
            t.initLogger("transferbase")
            cmd = "/bin/ls -l ."
            rv = t.transferData(cmd)
            print rv
            assert str(rv.code) == "Success"
