# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import sys
import os
import shutil
import hashlib

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "test":
    raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)

from TransferModules.RsyncTransfer import RsyncTransfer
import MiStaMoverController

if __name__ == '__main__':
    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--runPipe":
            h1 = hashlib.md5()
            shutil.copy("test/testfiles/testfile.bak", "test/testfiles/testfile")
            try:
                f1 = open("test/testfiles/testfile", "r")
                fs1 = f1.read()
                f1.close()
                h1.update(fs1)
            except Exception, e1:
                print str(e1)
            hd1 = h1.digest()
            s = MiStaMoverController.MiStaMoverController("test/conf/rsync_global2.ini")
            d = s.dconfigs['rsync2']
            t = RsyncTransfer(d)
            rv = t.setupTransfer("testfile")
            assert str(rv.code) == "Success"
            if str(rv.code) == "Success":
                print "transfer ok"
                h2 = hashlib.md5()
                try:
                    f2 = open("test2/rsync2/testfile")
                    fs2 = f2.read()
                    f2.close()
                    h2.update(fs2)
                except Exception, e2:
                    print str(e2)
                hd2 = h2.digest()

                assert hd1 == hd2, "file hashes not equal"

                shutil.copy("test/testfiles/testfile.bak", "test/testfiles/testfile")
                try:
                    os.remove("test2/testfiles/testfile")
                except:
                    pass  
   
