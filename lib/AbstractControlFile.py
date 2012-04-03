# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os

class Invalid(Exception):
    pass

class FileExists(Exception):
    pass

class AbstractControlFile(object):
    """
    Simple class to read/write control file.

    Note that this base class contains read() and create() 
    that the calling code will actually call, but they rely on the
    subclass to provide certain helper functions.

    In particular, subclasses must provide:
      magic1, magic2: strings to put at start and end of file
      encode: method to turn input data into lines for the file
      decode: method to turn lines from the file into data    
    """
    def __init__(self, file_path, can_overwrite=False):
        self.file_path = file_path
        self.can_overwrite = can_overwrite

    def __del__(self):
        if hasattr(self, "f") and not self.f.closed:
            self.f.close()
        
    def stripNewline(self, line):        
        if line[-1] == '\n':
            line = line[:-1]
        return line

    def writeline(self, data):
        self.f.write("%s\n" % data)

    def readlines(self):
        """
        Read lines excluding (but checking) the 'magic' lines at start and end
        """
        try:
            self.f = open(self.file_path)
            lines = map(self.stripNewline, self.f.readlines())
            assert(lines[0] == self.magic1)
            assert(lines[-1] == self.magic2)
        except:
            raise Invalid(self.file_path)
        self.f.close()
        return lines[1 : -1]

    def writelines(self, data):
        """
        Write lines, adding on the 'magic' lines at start and end.
        """
        tmp_path = self.file_path + "_tmp"
        self.f = open(tmp_path, "w")
        self.writeline(self.magic1)
        for i in data:
            self.writeline(i)
        self.writeline(self.magic2)
        self.f.close()
        os.rename(tmp_path, self.file_path)
            
    def read(self):
        """
        Read the file, return decoded contents
        """
        lines = self.readlines()
        try:
            self.data = self.decode(lines)
            return self.data
        except:
            raise Invalid(self.file_path)

    def create(self, *args, **kwargs):
        """
        Create the file from input data
        """
        if not self.can_overwrite and os.path.exists(self.file_path):
            raise FileExists(self.file_path)
        data = self.encode(*args, **kwargs)
        self.data = data
        self.writelines(data)
