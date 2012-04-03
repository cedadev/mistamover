# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from AbstractControlFile import *


class ThankyouFile(AbstractControlFile):
    """
    Simple class to read/write thank you file.
    It contains the name of the receipt file that is being acknowledged.

    Lines of Thankyou file are:

        magic1
        basename_for_receipt_file
        magic2

    Note read() and create() are in base class; encode() and decode() 
    are helpers for them.
    """
    magic1 = "_start_stager_thankyou_"
    magic2 = "_end_stager_thankyou_"

    def encode(self, rcpt_file_name):
        return [rcpt_file_name]

    def decode(self, lines):
        (rcpt_file_name,) = lines
        return [rcpt_file_name]
        
    def getFileName(self):
        return self.data[0]


if __name__ == '__main__':

    import os

    fname = "myfile.tmp"
    os.system("rm -f %s" % fname)
    
    a1 = ThankyouFile(fname)
    a1.create("foo")
    os.system("cat %s" % fname)
    a2 = ThankyouFile(fname)
    print a2.read()
