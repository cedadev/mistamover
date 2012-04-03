# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from RsyncTransfer import RsyncTransfer
from RsyncNativeTransfer import RsyncNativeTransfer
from FtpTransfer import FtpTransfer
from GridFTPTransfer import GridFTPTransfer
class TransferBaseController:
    def __init__(self, config):
        self.config = config
        self.tp = self.config.get("outgoing.transfer_protocol")
  
    def transfer(self, f):
        if self.tp == "rsync_ssh":
            r = RsyncTransfer(self.config)
            r.setupTransfer(f)
        if self.tp == "rsync_native":
            r = RsyncNativeTransfer(self.config)
            r.setupTransfer(f)
        if self.tp == "ftp":
            r = FtpTransfer(self.config)
            r.setupTransfer(f)
        if self.tp == "gridftp":
            r = GridFTPTransfer(self.config)
            r.setupTransfer(f)
    
