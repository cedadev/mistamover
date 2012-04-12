# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import sys
import os

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "test":
    raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)


import StagerController
from TransferModules.FtpTransfer import FtpTransfer
from TransferModules.TransferUtils import TransferUtils
from ReceiptFile import ReceiptFile
if __name__ == '__main__':
    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--checkVars":
            s = MiStaMoverController.MiStaMoverController("test/conf/ftp_global.ini")
            d = s.dconfigs['ftp']
            r = FtpTransfer(d)
            r.checkVars()
            r.setFile("testfile")
            print r.setupStopFileCmd()
            print r.setupPushCmd()
            print r.setupPullRcptCmd()
            # create a dummy receipt file
            rf = ReceiptFile(r.config.get("data_stream.directory") + "/" + "." + r.getFile() + "." + \
                r.config.get("outgoing.receipt_file_extension"))
            data_file_name = r.getFile()
            rcpt_args = [data_file_name] + [0, 12, "ac761519fdaf77899202c34692d64c98"]
            ts = TransferUtils.timeStamp()
            thankyou_file_name = (".%s.%s%s" %
                              (r.getFile(),
                               ts,
                               r.config.get("outgoing.thankyou_file_extension")))
            kwargs = {"thankyou_file": thankyou_file_name}
            rf.create(*rcpt_args, **kwargs)
            r.rcpt_file_path = "test/." + r.getFile() + "." + r.config.get("outgoing.receipt_file_extension") 
            print r.setupPushThanksCmd()
            try:
                os.remove("test/testfiles/." + r.getFile() + "." + r.config.get("outgoing.control_file_extension"))
                os.remove("test/testfiles/." + r.getFile() + "." + r.config.get("outgoing.receipt_file_extension"))
            except Exception, ex:
                pass
