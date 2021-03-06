# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import sys
import os
import tempfile

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "test":
  raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)

from TransferModules.TransferBase import TransferBase
#from LoggerClient import LoggerClient
import MiStaMoverController

if __name__ == '__main__':
    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--runPipe":
            s = MiStaMoverController.MiStaMoverController("test/conf/gridftp_global.ini")
            t = TransferBase()
            t.setConfig(s.gconfig)
            t.initLogger("transferbase")
            tf, name = tempfile.mkstemp()
            os.write(tf, t.config.get("gridftp.password"))
            os.fsync(tf)
            cmd = "myproxy-logon -S -s " + t.config.get("gridftp.proxy") + " -l " + t.config.get("gridftp.username") + \
                " < " + name
            print cmd, name
            rv = t.transferData(cmd)
            try:
                os.close(tf)
                os.remove(name)
            except:
                pass
            print rv
            assert str(rv.code) == "Success"
        if sys.argv[1] == "--runPipeFail":
            s = MiStaMoverController.MiStaMoverController("test/conf/gridftp_global.ini")
            t = TransferBase()
            t.setConfig(s.gconfig)
            t.initLogger("transferbase")
            tf, name = tempfile.mkstemp()
            os.write(tf, t.config.get("gridftp.password"))
            os.fsync(tf)
            cmd = "1myproxy-logon -S -s " + t.config.get("gridftp.proxy") + " -l " + t.config.get("gridftp.username") + \
                " < " + name
            print cmd, name
            rv = t.transferData(cmd)
            try:
                os.close(tf)
                os.remove(name)
            except:
                pass
            print rv
            assert str(rv.code) == "Failure"
            print "Success - a command that is not present causes an error to be raised"
