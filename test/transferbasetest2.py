# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import sys
import os
import os.path

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "test":
    raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)

from TransferModules.TransferBase import TransferBase

# mock up an info method
def info(b):
    print b

if __name__ == '__main__':
    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--runPipe":
            t = TransferBase()
            # mock up an info method
            setattr(t, 'info', info)
            cmd = "rsync -avz test/testfile test/testfile.new"
            rv = t.transferData(cmd)
            print rv
            assert str(rv.code) == "Success"
            if os.path.exists("test/testfile.new"):
                print "transfer ok"
                try:
                    os.remove("test/testfile.new")
                except:
                    pass
            else:
                print "transfre fail"
