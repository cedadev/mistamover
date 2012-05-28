# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from TransferBase import TransferBase
from TransferUtils import *
import os
import tempfile

import sys
this_dir = os.path.dirname(__file__)
top_dir = os.path.abspath(os.path.dirname(this_dir + "../"))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)

from Response import Response, ResponseCode
from ControlFile import ControlFile
from ReceiptFile import ReceiptFile
from ThankyouFile import ThankyouFile

class GridFTPTransferCertificate(TransferBase):
    """
    GridFTP transfer type
    """
    def __init__(self, config): 
        self.config = config
        self.cmd = self.config.get("gridftp_certificate.cmd");
    
        self.setConfig(config)
    
        self.short_name = "gridftp"
        self.initLogger(self.short_name)

        self.thankyou_file_path = None
        self.rcpt_file_path = None
        self.ctl_file_path = None

    # this is called by TransferModule
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
        # set up a control file
        if self.config.get("outgoing.target_uses_arrival_monitor"):
            # set up a control file
            item_name = self.getFile()
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

        f = self.getFile()
        gftp = self.cmd
        if self.config.get("outgoing.target_uses_arrival_monitor") == False:
            gftp += " -sync -sync-level 3"
        pushcmd = (gftp + " " + self.config.get("data_stream.directory") + "/"
            + f + " gsiftp://" + self.config.get("outgoing.target_host") + ":" 
            + str(self.config.get("gridftp.port")) + "//" +  
            self.config.get("outgoing.target_dir") + "/" + f)
        if self.config.get("outgoing.target_uses_arrival_monitor"):
            pushcmd += ("; " + gftp + " " + self.config.get(
                "data_stream.directory") + "/" + ctl_file_name + " gsiftp://"
                + self.config.get("outgoing.target_host") + ":" +
                str(self.config.get("gridftp.port")) +
                self.config.get("outgoing.target_dir") + "/" + ctl_file_name)
        self.info("setupPushCmd %s " % pushcmd)
        return pushcmd

    def setupPullRcptCmd(self):
        '''
        called by TransferBase to setup the command that pulls receipt files 
        from the target
        '''
        gftp = self.cmd
        pullrcpt = (gftp + " gsiftp://" + self.config.get("outgoing.target_host")
            + ":" + str(self.config.get("gridftp.port")) + "//" + self.config.get(
            "outgoing.target_dir") + "/" + self.rcpt_file_name + " " +
            self.config.get("data_stream.directory") + "/" + self.rcpt_file_name)
        return pullrcpt

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
        gftp = self.cmd
        try:
            rcpt = ReceiptFile(self.rcpt_file_path)
            rcpt_data = rcpt.read()
        except Exception, err:
            self.info("push thanks setup fail %s" % err)
            return ""
        thankyou_file_name = rcpt_data[4]
        thankyou_file_path = (TransferUtils.getPathInDir(thankyou_file_name,
            self.config.get("data_stream.directory")))
        self.thankyou_file_path = thankyou_file_path
        thankyou_file = ThankyouFile(thankyou_file_path)
        thankyou_file.create(self.rcpt_file_name)
        self.thankyou_file_path = thankyou_file_path
        thankyoucmd = (gftp + " " + self.config.get("data_stream.directory") +
            "/" + thankyou_file_name + " gsiftp://" + self.config.get(
            "outgoing.target_host") + ":" + str(self.config.get(
            "gridftp.port")) + "//" +  self.config.get("outgoing.target_dir")
            + "/" + thankyou_file_name)
        return thankyoucmd

    # this is called by TransferModule
    def setupStopFileCmd(self):
        '''
        called by TransferBase in order to create the command to check for stop
        files
        '''
        tf, name = tempfile.mkstemp()
        self.stopname = name
        self.stoptf = tf
        pullstop = (self.cmd + " gsiftp://" + self.config.get(
            "outgoing.target_host") + ":" + str(self.config.get("gridftp.port"))
            + "//" + self.config.get("outgoing.target_dir") + "/" +
            self.config.get("outgoing.stop_file") + " " + name)
        self.info("setupStopFileCmd %s " % pullstop)
        return pullstop

    def checkVars(self):
        try:
            os.environ['GLOBUS_LOCATION']
        except:
            raise Exception("GLOBUS_LOCATION environment variable is not set")
        try:
            os.environ['X509_USER_PROXY']
        except:
            raise Exception("X509_USER_PROXY environment variable is not set")
        if not self.config.checkSet("gridftp.port"):
            raise Exception("gridftp.port is not set")
        if not self.config.checkSet("gridftp.cmd"):
            raise Exception("gridftp.cmd is not set")
        # the following 3 are needed for setting up a proxy credential
        if not self.config.checkSet("gridftp.username"):
            raise Exception("gridftp.username is not set")
        if not self.config.checkSet("gridftp.password"):
            raise Exception("gridftp.password is not set")
        if not self.config.checkSet("gridftp.proxy"):
            raise Exception("gridftp.proxy is not set")
        if not self.config.checkSet("gridftp.port"):
            raise Exception("gridftp.port is not set")
        # these are required for transfer
        if not self.config.checkSet("outgoing.target_dir"):
            raise Exception("outgoing.target_dir is not set")
        if not self.config.checkSet("outgoing.target_host"):
            raise Exception("outgoing.target_host is not set")
        if not self.config.checkSet("data_stream.directory"):
            raise Exception("data_stream.directory is not set")

    # this is the entry point for the module
    def setupTransfer(self, f):
        self.setFile(f)
        if not self.checkFileExists(self.config.get("data_stream.directory") + "/" + f):
            rc = ResponseCode(False)
            grv = Response(rc, "Not attempting file transfer")
            return grv
        file_name = (TransferUtils.getPlainFileName(self.config.get(
            "data_stream.directory"), f, self.config.get("outgoing.dir_size_limit")))
        if not file_name:
            (TransferUtils.quarantine(f, self.config.get("data_stream.directory"),
                 self.config.get("outgoing.quarantine_dir")))
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
            r = Response(rc, "not all required variables in GridFTPTransfer are set : ", str(ex))
            self.info("not all required variables in GridFTPTransfer are set : %s " % str(ex))
            return r
        self.setStopReturnCode(1)
        self.setStopError("failed: No such file or directory")

        # in order to use grid ftp we need a valid credential
        self.info("GridFTPTransfer checking credentials")
        checkCredential = "grid-proxy-info -exists"
        grv = self.transferData(checkCredential)
        if str(grv.code) == "Failure":
            # try and set a new credential
            self.info("GridFTPTransfer checking credentials failed %s" % grv.data)
            tf, name = tempfile.mkstemp()
            os.write(tf, self.config.get("gridftp.password"))
            os.fsync(tf)
            setupCredential = ("myproxy-logon -S -s " + self.config.get(
                "gridftp.proxy") + " -l " + self.config.get("gridftp.username")
                + " < " + name)
            grv = self.transferData(setupCredential)
            try:
                os.close(tf)
                os.remove(name)
            except:
                pass
            if str(grv.code) == "Failure":
                return grv

        grv = self.waitForStopFile()
        if str(grv.code) == "Success":
            grv = self.pushData()
            self.info(" rv = %s " % str(grv.code))
            self.info("GridFTPTransfer exiting %s" % str(grv.code))
            self.info("Successfully sent: %s; size: %s" % (self.getFile(), filesize))
        return grv

