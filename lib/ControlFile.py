# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from AbstractControlFile import *


class ControlFile(AbstractControlFile):
    """
    Simple class to read/write control file.

    Note read() and create() are in base class; encode() and decode() 
    are helpers for them.

    Lines of control file are:

        magic1
        data_file_name
        expected_size_in_bytes
        expected_md5_checksum
        basename_requested_for_receipt_file
        magic2
    """
    magic1 = "_start_stager_ctrl_data_"
    magic2 = "_end_stager_ctrl_data_"

    def encode(self, filename, size, cksum, rcptname=None):
        if not rcptname:
            rcptname = filename + ".rcpt"
        return [filename, size, cksum, rcptname]

    def decode(self, lines):
        data_file_name, sizeStr, checksum, rcpt_file_name = lines
        return [data_file_name, int(sizeStr), checksum, rcpt_file_name]
        
    def getFileName(self):
        return self.data[0]

    def getFileSize(self):
        return self.data[1]

    def getFileChecksum(self):
        return self.data[2]

    def getRcptName(self):
        return self.data[3]


if __name__ == '__main__':

    import os

    fname = "myfile.tmp"
    os.system("rm -f %s" % fname)
    
    a1 = ControlFile(fname)
    a1.create("foo", 34, "a25902q5390", "foo.rcpt")
    os.system("cat %s" % fname)
    a2 = ControlFile(fname)
    path, size, cksum, rcptfile = a2.read()
    print "-- %s -- %d -- %s -- %s --" % (path, size, cksum, rcptfile)
    print a2.getFileSize()
