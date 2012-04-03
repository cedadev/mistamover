#!/usr/bin/env python
# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import commands
import hashlib
import md5 as md5mod

class md5(object):

    def __init__(self, file):
        self.chksum = commands.getoutput("/usr/bin/md5sum %s" % file).split()[0].strip()

    def hexdigest(self):
        return self.chksum


if __name__ == "__main__":

    f = "md5_comparer.py"
    print md5(f).hexdigest()
    contents = open(f).read()
    print md5mod.md5(contents).hexdigest()
    print hashlib.md5(contents).hexdigest()

