# BSD Licence                                                                                               
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)                                        
# All rights reserved.                                                                                      
#                                                                                                           
# See the LICENSE file in the source distribution of this software for                                      
# the full license text.                                                                                    

import sys, os

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "unittests":
    raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "../lib")           
sys.path.append(lib_dir)

import ReceiptFile

if __name__ == '__main__':

    import os

    def test_receipt():
        fname = "rcptfile.tmp"
        os.system("rm -f %s" % fname)

        out1 = ReceiptFile.ReceiptFile(fname)
        out1.create("foo", ReceiptFile.SUCCESS, 123, "abc123", "foo.thanks")
        in1 = ReceiptFile.ReceiptFile(fname)
        data = in1.read()
        print data
        print in1.getFileSize()

        out2 = ReceiptFile.ReceiptFile(fname, can_overwrite = True)
        out2.create("bar", ReceiptFile.BAD_SIZE, 124)
        in2 = ReceiptFile.ReceiptFile(fname)
        data = in2.read()
        print data
        print in2.getFileSize()

    if len(sys.argv) == 2:
        if sys.argv[1] == "--receipt":
            test_receipt()
