# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
A simple subclass of zipfile.ZipFile that lets you
remove leading path element from the zipfile name.

Use exactly as for ZipFile except that on instantiaion you have the 
argument remove_prefix which is the prefix you want removed from all
paths in the zip file, and method writeWithoutPrefix() which will
be like ZipFile.write() except that it will remove the prefix
"""

from zipfile import *


class MyZipFile(ZipFile):
    """
    see module-level doc
    """
        
    def __init__(self, path, remove_prefix = '', *args, **kwargs):
        self.remove_prefix = remove_prefix
        self.prefix_length = len(remove_prefix)
        ZipFile.__init__(self, path, *args, **kwargs)

    def writeWithoutPrefix(self, fname, *args, **kwargs):
        aname = fname
        if self.remove_prefix and aname.startswith(self.remove_prefix):
            aname = aname[self.prefix_length :]
        return self.write(fname, arcname=aname, *args, **kwargs)
