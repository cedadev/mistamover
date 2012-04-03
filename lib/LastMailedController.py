# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
LastMailedController.py
=======================

Holds LastMailedController class.

"""

import os
import time


class LastMailedController(object):
    """
    Holds a class for managing whether we should send out a mail or not.
    """

    def __init__(self, last_mailed_file, interval_between_mails = 60):
        self.last_mailed_file = last_mailed_file
        self.lmf = self.last_mailed_file
        self.interval = interval_between_mails

        if not os.path.isfile(last_mailed_file):
            self.setLMTime()

    def shouldWeMail(self):
        """
        Main API call for this class. Returns a boolean.
        """
        try:
            previous = self.getLMTime()
        except:
            return False

        now = time.time()
        time_difference = now - previous

        if time_difference > self.interval:
            self.setLMTime()
            return True

        return False

    def getLMTime(self):
        try:
            tm = self._readLMFile()
        except:
            tm = 0.0

        return tm

    def setLMTime(self):
        tm = str(int(time.time()))
        self._writeLMFile(tm)

    def _readLMFile(self):
        f = open(self.lmf)
        tm = f.read().strip()
        f.close()

        tmfloat = float(tm)
        return tmfloat

    def _writeLMFile(self, tm):
        if os.path.isfile(self.lmf):
            os.chmod(self.lmf, 700)

        fout = open(self.lmf, "w")
        fout.write(tm)
        fout.close()

        os.chmod(self.lmf, 400)


if __name__ == "__main__":

    x = LastMailedController("lmf.txt", 5)
    print x.shouldWeMail()
    time.sleep(3)
    print x.shouldWeMail()
    time.sleep(7)
    print x.shouldWeMail()

