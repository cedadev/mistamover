# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from TransferBase import TransferBase
from TransferUtils import TransferUtils
import os
import tempfile
import time

import sys
this_dir = os.path.dirname(__file__)
top_dir = os.path.abspath(os.path.dirname(this_dir + "../"))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)

from Response import Response, ResponseCode
from ControlFile import ControlFile
from ReceiptFile import ReceiptFile
from ThankyouFile import ThankyouFile

class FtpTransfer(TransferBase):
    """
    Ftp transfer type
    """
    def __init__(self, config):
        self.config = config
        self.cmd = self.config.get("ftp.cmd");

        self.setConfig(config)

        self.short_name = "ftp"
        self.initLogger(self.short_name)

        self.thankyou_file_path = None
        self.rcpt_file_path = None
        self.ctl_file_path = None

    # called by TransferBase
    def setupStopFileCmd(self):
        '''
        called by TransferBase in order to create the command to check for stop
         files
        '''
        tf, name = tempfile.mkstemp()
        os.write(tf, "user " + self.config.get("ftp.username") + " " + \
            self.config.get("ftp.password") + "\n")
        os.write(tf, "cd " + self.config.get("outgoing.target_dir") + "\n")
        os.write(tf, "lcd " + self.config.get("data_stream.directory") + "\n")
        os.write(tf, "get " + self.config.get("outgoing.stop_file") + "\n")
        os.write(tf, "exit\n")
        os.fsync(tf)
        os.close(tf)
        pullstop = "/usr/bin/ftp -n " + self.config.get("outgoing.target_host") \
             + " < " + name
        self.info("setupStopFileCmd %s" % pullstop)
        self.stoptf = tf
        self.stopname = name
        return pullstop

    # called by TransferBase
    def setupPushCmd(self):
        '''
        called by TransferBase in order to create a push command
        '''
        if self.ctl_file_path != None:
            try:
                os.remove(self.ctl_file_path)
            except:
                pass
        if self.rcpt_file_path != None:
            try:
                os.remove(self.rcpt_file_path)
            except:
                pass
        # set up a control file
        item_name = self.getFile()
        item_path = os.path.join(self.config.get("data_stream.directory"), \
            os.path.basename(item_name))
        ctl_file_name = ".%s.%s" % (item_name, self.config.get( \
            "outgoing.control_file_extension"))
        ctl_file_path = os.path.join(self.config.get("data_stream.directory"), \
            os.path.basename(ctl_file_name))
        self.ctl_file_path = ctl_file_path
        item_size = os.path.getsize(item_path)
        item_cksum = TransferUtils.calcChecksum(item_path)                                               
        ts = "%.2f" % time.time()
        rcpt_file_name = ".%s.%s.%s" % (item_name, ts, self.config.get( \
            "outgoing.receipt_file_extension"))
        ctl_file = ControlFile(ctl_file_path, can_overwrite=True)
        ctl_file.create(item_name, item_size, item_cksum, rcpt_file_name)
        self.rcpt_file_name = rcpt_file_name
        self.rcpt_file_path = TransferUtils.getPathInDir(rcpt_file_name, \
            self.config.get("data_stream.directory"))
        # set up ftp transfer + control file
        tf, name = tempfile.mkstemp()
        os.write(tf, "user " + self.config.get("ftp.username") + " " + \
            self.config.get("ftp.password") + "\n")
        os.write(tf, "cd " + self.config.get("outgoing.target_dir") + "\n")
        os.write(tf, "lcd " + self.config.get("data_stream.directory") + "\n")
        os.write(tf, "put " + self.getFile() + "\n")
        if self.config.get("outgoing.target_uses_arrival_monitor"):
            os.write(tf, "put " + ctl_file_name + "\n")
        os.write(tf, "exit\n")
        os.fsync(tf)
        os.close(tf)
        #print self.getTargetHost(), self.getTarget(), self.getDatasetName(), self.config.get("dataset.directory"), self.getFile(), ctl_file_name
        pushcmd = "/usr/bin/ftp -n " + self.config.get("outgoing.target_host") \
            + " < " + name
        self.info("setupPushCmd %s" % pushcmd)
        self.pushtf = tf
        self.pushname = name
        return pushcmd

    # called by TransferBase
    def setupPullRcptCmd(self):
        '''
        called by TransferBase to setup the command that pulls receipt files 
        from the target
        '''
        tf, name = tempfile.mkstemp()
        os.write(tf, "user " + self.config.get("ftp.username") + " " + \
            self.config.get("ftp.password") + "\n")
        os.write(tf, "cd " + self.config.get("outgoing.target_dir") + "\n")
        os.write(tf, "lcd " + self.config.get("data_stream.directory") + "\n")
        os.write(tf, "get " + self.rcpt_file_name + "\n")
        os.write(tf, "exit\n")
        os.fsync(tf)
        os.close(tf)
        pullrcpt = "/usr/bin/ftp -n " + self.config.get("outgoing.target_host") \
            + " < " + name
        self.info("setupPullRcptCmd %s" % pullrcpt)
        self.pulltf = tf
        self.pullname = name
        return pullrcpt

    # called by TransferBase
    def setupPushThanksCmd(self):
        '''
        called by TransferBase to setup the command that pushes a ThankYou file 
        to the target
        '''
        if self.thankyou_file_path != None:
            try:
                os.remove(self.thankyou_file_path)
            except:
                pass
        # there should be no issue here as this is only called after
        # a receipt file has been proven to be valid
        #rcpt_err = None
        try:
            rcpt = ReceiptFile(self.rcpt_file_path)
            rcpt_data = rcpt.read()
        except Exception, err:
            #rcpt_err = "bad receipt file: %s" % err
            self.info("push thanks setup fail %s" % err)
            return ""
        thankyou_file_name = rcpt_data[4]
        thankyou_file_path = TransferUtils.getPathInDir(thankyou_file_name, \
            self.config.get("data_stream.directory"))
        self.thankyou_file_path = thankyou_file_path
        thankyou_file = ThankyouFile(thankyou_file_path)
        thankyou_file.create(self.rcpt_file_name)
        self.thankyou_file_path = thankyou_file_path
        # set up ftp transfer + thankyou file
        tf, name = tempfile.mkstemp()
        os.write(tf, "user " + self.config.get("ftp.username") + " " + \
            self.config.get("ftp.password") + "\n")
        os.write(tf, "cd " + self.config.get("outgoing.target_dir") + "\n")
        os.write(tf, "lcd " + self.config.get("data_stream.directory") + "\n")
        os.write(tf, "put " + thankyou_file_name + "\n")
        os.write(tf, "exit\n")
        os.fsync(tf)
        os.close(tf)
        thankyoucmd = "/usr/bin/ftp -n " + self.config.get( \
            "outgoing.target_host") + " < " + name
        self.info("setupThanksCmd %s" % thankyoucmd)
        self.thktf = tf
        self.thkname = name
        return thankyoucmd

    def checkVars(self):
        if not self.config.checkSet("ftp.cmd"):
            raise Exception("ftp.cmd is not set")
        if not self.config.checkSet("outgoing.target_dir"):
            raise Exception("outgoing.target_dir is not set")
        if not self.config.checkSet("outgoing.target_host"):
            raise Exception("outgoing.target_host is not set")
        if not self.config.checkSet("data_stream.directory"):
            raise Exception("data_stream.directory is not set")
        # get a list of keys that should be set if we are using
        # arrival Monitor
        keys = []
        keys.append("outgoing.receipt_file_extension")
        keys.append("outgoing.control_file_extension")
        keys.append("outgoing.thankyou_file_extension")
        key = "outgoing.target_uses_arrival_monitor"
        rv = self.config.checkSetIf(key, True, keys)
        rk = []
        if rv != None:
            for v in rv:
                rk.append(v + " is not set\n")
            rks = "".join(rk)
            raise Exception("%c" % rks)
    
    # entry point for module  
    def setupTransfer(self, f):
        self.setFile(f)
        #print "current file name = ", f
        file_name = TransferUtils.getPlainFileName(self.config.get( \
            "data_stream.directory"), f, self.config.get( \
            "outgoing.dir_size_limit"))
        #print "file_name from getplain filename = ", file_name
        if not file_name:
            TransferUtils.quarantine(f, self.config.get("data_stream.directory"), \
                 self.config.get("outgoing.quarantine_dir"))
            grv = Response.failure("Did not attempt transfer of %s" % f)
            self.info("Did not attempt transfer of %s" % f)
            return grv
        else:
            self.setFile(os.path.basename(file_name))

        fn = os.path.join(self.config.get("data_stream.directory"), file_name)
        filesize = os.path.getsize(fn)

        try:
            self.checkVars()
        except Exception, ex:
            rc = ResponseCode(False)
            r = Response(rc, "not all variables in FtpTransfer ", str(ex))
            self.info("not all variables in FtpTransfer %s " % str(ex))
            return r
        f = self.getFile()
        pullstop = self.setupStopFileCmd()
        self.setStopReturnCode(0)
        self.setStopError("No such file or directory")

        grv = self.waitForStopFile()
        if str(grv.code) == "Success":
            os.remove(self.stopname)
            # get rid of any stop files we may have retrieved
            if os.path.exists(self.config.get("data_stream.directory") + "/" + \
                self.config.get("outgoing.stop_file")):
                os.remove(self.config.get("data_stream.directory") + "/" +  \
                    self.config.get("outgoing.stop_file"))

            grv = self.pushData()

            # remove temp files
            try:
                os.remove(self.pushname)
                os.remove(self.pullname)
                os.remove(self.thkname)
            except Exception, ex:
                print str(ex)

            # remove transfer control files
            try:
                os.remove(self.thankyou_file_path)
                os.remove(self.rcpt_file_path)
                os.remove(self.ctl_file_path)
            except Exception, ex:
                print str(ex)

            self.info(" rv = %s " % str(grv.code))

        if str(grv.code) == "Success":
            self.info("Successfully sent: %s; size: %s bytes" % (self.getFile(), \
                filesize))
        return grv

