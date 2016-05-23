# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os
from subprocess import Popen, PIPE
import time
import shutil

import sys
this_dir = os.path.dirname(__file__)
top_dir = os.path.abspath(os.path.dirname(this_dir + "../"))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)

from Response import Response, ResponseCode
from LoggerClient import LoggerClient
from StatusFlag import status
from Daemon import weWereSignalled
from ReceiptFile import ReceiptFile

class TransferBase:
    """
    Abstract Base class for all transfer types
    This class uses command strings obtained from derived classes to push and pull
    files according to the following protocol

    No Arrival Monitor :-
    
    source           pull stop file		   target
    t0 <------------------------------------------- t1
                     push data file
    t2 ------------------------------------------>> t3

    In the above protocol - the stop file is pulled from 
    the target until the source detects that the stop 
    file is no longer present at which point the data
    file is pushed to the target

    With Arrival Monitor :-

    source           pull stop file                target
    t0 <------------------------------------------- t1
                     push data file
    t2 ------------------------------------------>> t3
                     push control file
    t4 -------------------------------------------> t5
                     pull receipt file
    t6 <------------------------------------------- t7
                     push thankyou file
    t8 -------------------------------------------> t8

    In this case we start as begore - waiting for the stop
    file on the target side to be not present.
    Then the data file followed by a control file is sent
    once the control file is received by the target, the
    target creates a receipt file
    Once the receipt file is pulled to the source, the
    source pushes a thankyou file and the transfer is
    considered to be finished
    """
    __stopReturnCode = None
    __stopError = None
    __file = None
    __mirror = None

    def setStopReturnCode(self, c):
        self.__stopReturnCode = c

    def getStopReturnCode(self):
        return self.__stopReturnCode

    def setStopError(self, e):
        self.__stopError = e

    def getStopError(self):
        return self.__stopError

    def setFile(self, f):
        self.__file = f

    def getFile(self):
        return self.__file

    def setConfig(self, c):
        self.config = c

    def getConfig(self):
        return self.config

    def __del__(self):
        self.info("transferbase exit")

    def checkFileExists(self, f):
        try:
            if not os.path.exists(f):
                self.warn("Trying to transfer a file (" + f + ") that does not exist")
                return False 
        except Exception, ex:
            self.warn("Trying to transfer a file (" + f + ") that does not exist")
            return False
        return True

    def transferData(self, cmd):
        """
        transferData via subprocess.popen
        all data is piped back through stdout and stderr
        This method does not know about the concept of push or pull, it 
        only executes the command string given to it
        """
        grc = None
        grv = None 
        self.info("transferData")
        if cmd == None:
            grc = ResponseCode(False)
            grv = Response(grc, "cmd was None")
            return grv
        try:
            p = Popen(cmd, shell=True, bufsize=1024, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            # communicate waits for process to terminate
            out = repr(stdout)
            err = repr(stderr)
            rv = str(p.returncode)
            if (rv == "0"):
                # transfer went ok
                grc = ResponseCode(True)
                grv = Response(grc, cmd, out)
                self.info("transferData for %s OK " % cmd)
            else:
                # transfer failed in some way
                grc = ResponseCode(False)
                grv = Response(grc, rv, err)
                self.info("transferData for %s Failed " % cmd)
        except Exception, ex:
            grc = ResponseCode(False)
            grv = (Response(grc, "An exception occurred during  transferData ",
                str(ex)))
            self.info("transferData for %s raised exception %s " % cmd, str(ex))
        return grv

    def checkUSR1(self):
        grv = None
        if weWereSignalled("USR1"):
            self.info("stop requested by signal")
            self.status = status.STOPPED
            grc = ResponseCode(False)
            grv = Response(grc, "pullReceipt stopped by SIGUSR1")
        return grv

    def initLogger(self, short_name):
        """
        Initialise the logger client module, and then log a single line
        that says "startup"
        """
        dset_name = self.config.get("data_stream.name")
        if self.config.checkSet("global.debug_on"):
            debug_on = self.config.get("global.debug_on")
        else:
            debug_on = False
     
        self.logger = LoggerClient(
            self.getConfig(),
            tag = "%s_%s" % (short_name, dset_name),
            name = "%s for data_stream %s" % (short_name, dset_name),
            debug_on = debug_on)
        # import some methods from the logger
        self.logger.exportMethods(self)
        self.info("startup")

    def deleteOrWarn(self, filename):
        '''
        remove files after they have been transfered or warn
        if for any reason they cannot be deleted
        '''
        self.debug("Running: 'deleteOrWarn' method")
        try:
            self.info("Removing local path: %s " % filename)
            if os.path.isdir(filename):
                shutil.rmtree(filename)    
            else:
                os.remove(filename)
            self.info("Removed: %s" % filename)
        except Exception, ex:
            self.warn("Could not delete %s" % filename)
            (self.info("'deleteOrWarn' method raised exception %s for %s" % (str(ex), filename)))

    def waitForStopFile(self):
        """
        wait until a stop file is no longer present on the
        target machine - we only push data when we are allowed 
        to do so
        """
        self.info("waitForStopFile")
        pullstop = self.setupStopFileCmd()
        stopFilePresent = True
        grc = ResponseCode(True)
        grv = Response(grc, None)
        # wait until the underlying protocol tells us that no file exists
        # - the message we look for is defined by self.getStopError()
        while stopFilePresent:
            srv = self.checkUSR1()
            if srv != None: return srv

            rv = self.transferData(pullstop)
            if rv.data.find(self.getStopError()) != -1:
                stopFilePresent = False
                (self.info("pull stop %s : Success, .stop file not present" %
                    (pullstop)))
            else:
                time.sleep(self.config.get("outgoing.stop_file_poll_interval"))
                self.info("waitForStopFile sleeping")   
        return grv

    def pushData(self):
        """
        take the push data command and call transferData
        if we are using an arrival Monitor then send a 
        conf file, pull a receipt file and then push
        a thankyou file
        """
        self.info("pushData")
        grv = self.checkUSR1()
        if grv != None: return grv

        tries = 0
        grv = None

        # set a default if non exists
        if not self.config.checkSet("outgoing.retry_count"):
            self.config.set("outgoing.retry_count", 3)

        while tries < self.config.get("outgoing.retry_count"):
            grs = self.checkUSR1()
            if grs != None: return grs

            pushcmd = self.setupPushCmd()
            self.info("pushData %s " % pushcmd)
            rv = self.transferData(pushcmd)
            if str(rv.code) != "Success":
                tries += 1
                if grv == None: grv = rv
                else: grv += rv
                time.sleep(self.config.get("global.general_poll_interval"))
                self.info("pushData trying transfer again")
            else:
                # the push succeeded - if we use arrivalMonitor we also need to
                # do that before we return
                if self.config.get("outgoing.target_uses_arrival_monitor"):
                    self.info("pushData succeeded - pulling receipt")
                    time.sleep(self.config.get("global.general_poll_interval"))
                    rrv = self.pullReceipt()
                    if grv == None: grv = rrv
                    else: grv += rrv
                    if str(rrv.code) == "Success":
                        # do thanksyou
                        self.pushThankYou()
                        self.info("pushData thankyou file sent ok")
                        break
                else:
                    if grv == None: grv = rv
                    else: grv += rv
                    self.info(" pushdata grv = %s " % str(grv.code))
                    if str(grv.code) == "Success":
                        if self.__mirror != True:
                            (self.deleteOrWarn(self.config.get(
                                "data_stream.directory") + "/" +
                                self.getFile()))
                    return grv
        self.info(" pushdata grv = %s " % str(grv.code))
        if str(grv.code) == "Success":
            if self.__mirror != True:
                (self.deleteOrWarn(self.config.get(
                    "data_stream.directory") + "/" + self.getFile()))
        return grv

    def pullReceipt(self):
        """
        pull a receipt file using transferData
        """
        self.info("pullReceipt")
        grv = self.checkUSR1()
        if grv != None: return grv

        pullrcpt = self.setupPullRcptCmd()
        self.info("pullReceipt %s " % pullrcpt)
        tries = 0
        grv = None
        while tries < self.config.get("outgoing.receipt_file_poll_count"):
            srv = self.checkUSR1()
            if srv != None: return srv

            rv = self.transferData(pullrcpt)
            if str(rv.code) != "Success" or rv.data.find(self.getStopError()) != -1:
                tries += 1
                rv.code = ResponseCode(False)
                if grv == None: grv = rv
                else: grv += rv
                time.sleep(self.config.get("outgoing.receipt_file_poll_interval"))
                self.info("pullReceipt trying receipt transfer again")
            else:
                # the pull receipt succeeded
                # check it is valid
                rcpt_err = None
                try:
                    rcpt = ReceiptFile(self.rcpt_file_path)
                    rcpt.read()
                    if grv == None: grv = rv
                    else: grv += rv
                    return grv
                except Exception, err:
                    rcpt_err = "bad receipt file: %s" % err
                    self.info("pull receipt raised exception : %s " % rcpt_err)
                    if grv == None: grv = rv
                    else: grv += rv
                    return grv
        return grv

    def pushThankYou(self):
        """
        push a thankyou file using transferData
        """
        self.info("pushThankyou")
        grv = self.checkUSR1()
        if grv != None: return grv

        pushthks = self.setupPushThanksCmd()
        self.info("pushThankYou %s " % pushthks)
        rv = self.transferData(pushthks)
        return rv

    # the following methods are implemented by the derived class
    def setupTransfer(self, f):
        raise NotImplementedError("Should have implemented this")

    def setupPushCmd(self):
        raise NotImplementedError("Should have implemented this")

    def setupStopFileCmd(self):
        raise NotImplementedError("Should have implemented this")
   
    def setupPullRcptCmd(self):
        raise NotImplementedError("Should have implemented this")

    def setupPushThanksCmd(self):
        raise NotImplementedError("Should have implemented this")
