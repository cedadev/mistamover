# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import time
import os

import LoggerClient
import Daemon
from FileUtils import futils
from StatusFlag import status


class AbstractDatasetController(object):

    """
    Base class for DatasetTransferController, TransferUnitController,
    and DatasetArrivalMonitor.
    """

    def __init__(self, dataset_config, debug_on=False):
        self.dconfig = dataset_config
        self.setVarsFromConfig()

        self.debug_on = debug_on
        self.initLogger(self.short_name, self.long_name)


    def __del__(self):
        self.info("exit abstract datasetcontroller")


    def setVarsFromConfig(self):
        """
        For convenience, set some instance variables based on the config 
        file. Typically the subclass will override this method with one 
        which adds further variables and then calls this base class method.
        """
        self.status = self.dconfig.get("data_stream.status")
        self.dataset_dir = self.dconfig.get("data_stream.directory")
        self.quarantine_dir = self.dconfig.get("outgoing.quarantine_dir")
        self.poll_interval = self.dconfig.get("global.general_poll_interval")

    def updateStatusAndConfig(self):
        """
        Updates the status and config, based on any editing of config files
        and/or signals received.
        """

        if self.dconfig.rereadIfUpdated():
            self.setVarsFromConfig()
            self.info("config file reread")

        if self.status == status.STOPPED:
            self.info("stop requested in config")

        elif Daemon.weWereSignalled("USR1"):
            self.info("stop requested by signal")
            self.status = status.STOPPED


    # listDir moved to FileUtils - leave a wrapper here
    def listDir(self, *args, **kwargs):
        return futils.listDir(*args, **kwargs)

        
    def initLogger(self, short_name, long_name):
        """
        Initialise the logger client module, and then log a single line
        that says "startup"
        """
        dset_name = self.dconfig.name
        self.logger = LoggerClient.LoggerClient(
            self.dconfig, 
            tag = "%s_%s" % (short_name, dset_name),
            name = "%s for data_stream %s" % (long_name, dset_name),
            debug_on=self.debug_on)

        # import some methods from the logger
        self.logger.exportMethods(self)
       
        self.info("startup")        

    
    def getPathInDir(self, filename, dirname):
        """
        Return full path in specified directory
        """
        # filename should not contain "/" so we only take its basename
        return os.path.join(dirname, os.path.basename(filename))        


    def getPathInDataDir(self, filename):
        """
        Return full path in data_stream directory
        """
        return self.getPathInDir(filename, self.dataset_dir)


    def listDataDir(self, *args, **kwargs):
        """
        List data_stream directory. Note that the file listing calls a 
        function that defaults to excluding dotfiles (see FileUtils.listDir)
        """
        self.info("Listing contents of data_stream dir: %s" % self.dataset_dir)
        return self.listDir(self.dataset_dir, *args, **kwargs)
    

    def timeStamp(self):
        """
        A timestamp that is designed to be part of a filename to ensure
        uniqueness.
        """
        return "%.2f" % time.time()


    def deleteOrWarn(self, filename):
        try:
            os.remove(filename)
        except:
            self.warn("Could not delete %s" % filename)
