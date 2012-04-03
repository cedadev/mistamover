# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from AbstractControlFile import *

SUCCESS = 0
BAD_SIZE = 1
BAD_CKSUM = 2
IO_ERROR = 3
NO_SUCH_FILE = 4
status_description = { 0: "success",
                       1: "data file has bad size",
                       2: "data file has bad checksum",
                       3: "I/O error reading data file",
                       4: "data file does not exist" }
_all_status_codes = status_description.keys()



class ReceiptFile(AbstractControlFile):
    """
    Class wrapper around a file that confirms a file size and check sum,
    and the path name of a receipt acknowledgment ('thank you') file.

    create() requires [filename, status, size, checksum]
    likewise read() returns these

    Note read() and create() are in base class; encode() and decode() 
    are helpers for them.
    
    Lines of receipt file are:

        magic1
        data_file_name
        numerical_status (see codes at top of module)
        actual_size_in_bytes (if applicable else empty line)
        actual_md5_checksum (if applicable else empty line)
        basename_requested_for_thankyou_file
        magic2

    """
    magic1 = "_start_stager_receipt_data_"
    magic2 = "_end_stager_receipt_data_"

    def describeStatus(self, status):
        try:
            return status_description[status]
        except KeyError:
            return "unknown status code %s" % status
    
    def encode(self, filename, status, size = -1, cksum = "",
               thankyou_file = ""):
        assert status in _all_status_codes
        return [filename, status, size, cksum, thankyou_file]

    def decode(self, lines):
        filename = lines[0]
        status = int(lines[1])
        size = int(lines[2])
        cksum = lines[3]
        thankyou_file = lines[4]
        assert status in _all_status_codes
        return [filename, status, size, cksum, thankyou_file]

    def getFileName(self):
        return self.data[0]

    def getStatus(self):
        return self.data[1]

    def getFileSize(self):
        return self.data[2]

    def getFileChecksum(self):
        return self.data[3]

if __name__ == '__main__':
    
    import os

    fname = "rcptfile.tmp"
    os.system("rm -f %s" % fname)
    
    out1 = ReceiptFile(fname)
    out1.create("foo", SUCCESS, 123, "abc123", "foo.thanks")
    in1 = ReceiptFile(fname)
    data = in1.read()    
    print data
    print in1.getFileSize()

    out2 = ReceiptFile(fname, can_overwrite = True)
    out2.create("bar", BAD_SIZE, 124)
    in2 = ReceiptFile(fname)
    data = in2.read()    
    print data
    print in2.getFileSize()
