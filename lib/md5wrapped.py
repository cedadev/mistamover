# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import commands

class md5(object):

    def __init__(self, file):
        self.chksum = commands.getoutput("/usr/bin/md5sum %s" % file).split()[0].strip()

    def hexdigest(self):
        return self.chksum 


if __name__ == "__main__":

    print md5("lib/FileUtils.py")
