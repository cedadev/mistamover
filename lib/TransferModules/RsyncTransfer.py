# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from TransferBase import TransferBase
from TransferUtils import *
import os

import sys
this_dir = os.path.dirname(__file__)
top_dir = os.path.abspath(os.path.dirname(this_dir + "../"))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)

from Response import Response, ResponseCode
from ControlFile import ControlFile
from ReceiptFile import ReceiptFile
from ThankyouFile import ThankyouFile


class RsyncTransfer(TransferBase):
    """
    Rsync transfer type
    """
    def __init__(self, config): 
        self.config = config
        self.cmd = self.config.get("rsync_ssh.cmd")
    
        self.setConfig(config)
    
        self.short_name = "rsync"
        self.initLogger(self.short_name)

        self.thankyou_file_path = None
        self.rcpt_file_path = None
        self.ctl_file_path = None


    # this is called from the TransferBase
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
        f = self.getFile()
        if not self.checkFileExists(self.config.get("data_stream.directory") + "/" + f):
            return None
        if self.config.get("outgoing.target_uses_arrival_monitor"):
            item_name = f
            item_path = (os.path.join(self.config.get("data_stream.directory"), 
                os.path.basename(item_name)))
            ctl_file_name = (".%s.%s" % (item_name, self.config.get(
                "outgoing.control_file_extension")))
            ctl_file_path = (os.path.join(self.config.get(
                "data_stream.directory"), os.path.basename(ctl_file_name)))
            self.ctl_file_path = ctl_file_path
            item_size = os.path.getsize(item_path)
            item_cksum = TransferUtils.calcChecksum(item_path)
            ts = "%.2f" % time.time()
            rcpt_file_name = (".%s.%s.%s" % (item_name, ts, self.config.get(
                "outgoing.receipt_file_extension")))
            ctl_file = ControlFile(ctl_file_path, can_overwrite=True)
            ctl_file.create(item_name, item_size, item_cksum, rcpt_file_name)
            self.rcpt_file_name = rcpt_file_name
            self.rcpt_file_path = (TransferUtils.getPathInDir(rcpt_file_name,
                self.config.get("data_stream.directory")))

        rsc = self.cmd + " -avz "
        if self.config.get("rsync_ssh.use_checksum") == True:
            rsc += " --checksum "
        if self.config.get("rsync_ssh.check_size") == True:
            rsc += " --size-only "
        if not self.config.get("outgoing.target_uses_arrival_monitor"):
            pushcmd = (rsc + self.config.get("data_stream.directory") + "/" +
            f + " " + self.config.get("outgoing.target_host") + "://" +
            self.config.get("outgoing.target_dir") + "/" + f)
        else:
            pushcmd = (rsc + self.config.get("data_stream.directory") + "/"
            +f + " " + self.config.get("data_stream.directory") + "/" +
            ctl_file_name + " " + self.config.get("outgoing.target_host") +
            "://" + self.config.get("outgoing.target_dir") + "/")
        self.info("setupPushCmd %s " % pushcmd)
        return pushcmd

    # this is called from the TransferBase
    def setupStopFileCmd(self):
        '''
        called by TransferBase in order to create the command to check for 
        stop files
        '''
        listonly = self.cmd + " --list-only "
        pullstop = (listonly + self.config.get("outgoing.target_host") + "://" 
            + self.config.get("outgoing.target_dir") + "/" + "/" + 
            self.config.get("outgoing.stop_file"))
        self.info("setupStopFileCmd %s " % pullstop)
        return pullstop

    def setupPullRcptCmd(self):
        '''
        called by TransferBase to setup the command that pulls receipt files 
        from the target
        '''
        pullrcpt = (self.cmd + " " + self.config.get("outgoing.target_host")
            + "://" + self.config.get("outgoing.target_dir") + "/" +
            self.rcpt_file_name + " " + self.config.get(
            "data_stream.directory") + "/")
        self.info("setupPullRcptCmd %s" % pullrcpt)
        return pullrcpt

    def setupPushThanksCmd(self):
        '''
        called by TransferBase to setup the command that pushes a ThankYou 
        file to the target
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
        thankyou_file_path = (TransferUtils.getPathInDir(thankyou_file_name,
             self.config.get("data_stream.directory")))
        self.thankyou_file_path = thankyou_file_path
        thankyou_file = ThankyouFile(thankyou_file_path)
        thankyou_file.create(self.rcpt_file_name)
        self.thankyou_file_path = thankyou_file_path
        thankyoucmd = (self.cmd + " " + self.thankyou_file_path +
            self.config.get("outgoing.target_host") + "://" +
            self.config.get("outgoing.target_dir") + "/")
        return thankyoucmd

    def checkVars(self):
        if not self.config.checkSet("rsync_ssh.cmd"):
            raise Exception("rsync_ssh.cmd is not set")
        if not self.config.checkSet("outgoing.target_dir"):
            raise Exception("outgoing.target_dir is not set")
        if not self.config.checkSet("outgoing.target_host"):
            raise Exception("outgoing.target_host is not set")
        if not self.config.checkSet("rsync_ssh.transfer_mode"):
            raise Exception("rsync_ssh.transfer_mode in not set (must be either move OR mirror)")
        if not self.config.checkSet("data_stream.directory"):
            raise Exception("data_stream.directory is not set")

    # this is the entry point for the module
    def setupTransfer(self, f):
        self.setFile(f)

        if not self.checkFileExists(self.config.get("data_stream.directory") + "/" + f):
            rc = ResponseCode(False)
            grv = Response(rc, "Not attempting file transfer")
            return grv

        # if we are mirroring - then do not zip directories - (we pass False to getPlainFileName)
        if self.config.get("rsync_ssh.transfer_mode") == "mirror":
            self.mirror = True
            file_name = (TransferUtils.getPlainFileName(self.config.get(
                "data_stream.directory"), f, self.config.get(
                "outgoing.dir_size_limit"), False))
        else:
            file_name = (TransferUtils.getPlainFileName(self.config.get(
                "data_stream.directory"), f, self.config.get(
                "outgoing.dir_size_limit")))
        if not file_name:
            (TransferUtils.quarantine(f, self.config.get(
                "data_stream.directory"), self.config.get(
                "outgoing.quarantine_dir")))
            rc = ResponseCode(False)
            grv = Response(rc, "Did not attempt transfer of %s" % f)
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
            r = Response(rc, "not all variables in RsyncTransfer ", str(ex))
            self.info("not all variables in RsyncTransfer %s " % str(ex))
            return r

        self.setStopReturnCode(23)
        self.setStopError("failed: No such file or directory")

        grv = self.waitForStopFile()
        if str(grv.code) == "Success":
            grv = self.pushData()
            self.info(" rv = %s " % str(grv.code))
            self.info("RsyncTransfer exiting %s" % str(grv.code))

        if self.config.get("outgoing.target_uses_arrival_monitor"):
            # remove transfer control files
            try:
                os.remove(self.thankyou_file_path)
                os.remove(self.rcpt_file_path)
                os.remove(self.ctl_file_path)
            except Exception, ex:
                print str(ex)
        if str(grv.code) == "Success":
            if self.config.get("outgoing.transfer_mode") == "move":
                (self.info("Successfully sent: %s; size: %s" % (self.getFile(),
                    filesize)))
        return grv

