# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import time
import os
import signal 


from AbstractDatasetController import AbstractDatasetController
from FileUtils import futils
from StatusFlag import status
from TransferModules.TransferBaseController import TransferBaseController

class DatasetTransferController(AbstractDatasetController):
    """
    A sub-process controller to manage a data_stream.

    The dataset transfer controller will monitor the data_stream directory
    for files (or directories) appearing.  With each that it sees, it
    will use the transferToRemoteHost method from a TransferUnitController
    object to transfer it to the remote host.

    Note that the TransferUnitController stuff runs in *this* same process.
    It is not a separate process in the way that some of the other
    "Controllers" in stager are.  This means that for each file to be 
    transferred, it waits for completion before attempting the next one.
    This is desirable.  There is no attempt to rescan the directory before
    it has finished transferring (or attempting to transfer) the existing files.
    
    Note also that a key assumption is that any files created by the transfer
    unit controller for chatter with a remote arrival monitor will be 
    dot-files, and as such are excluded from the scan.  Also explicitly 
    excluded is the quarantine directory (which may otherwise appear under
    the data_stream directory).
    """

    short_name = "dtc"
    long_name = "dataset transfer controller"

    def setVarsFromConfig(self):
        self.completion_file = self.dconfig.get("data_stream.completion_file")
        AbstractDatasetController.setVarsFromConfig(self)


    def doSetup(self):
        futils.ensureDirExists(self.dataset_dir)
        self.tidyDatasetDir()

    def processTransfers(self):
        """
        Runs forever until status changes.
        """
        
        self.doSetup()
        
        if self.status == status.COMPLETE:
            return self.status

        self.status = status.RUNNING
        self.info("Processing Transfers...")

        tbc = TransferBaseController(self.dconfig)

        had_completion_file = False
        runLoop = True
        while runLoop == True:
 
            self.updateStatusAndConfig()
            tp = self.dconfig.get("outgoing.transfer_protocol")
            if tp != "none":
                if (self.dconfig.checkSet("outgoing.target_dir") == False or
                    self.dconfig.checkSet("outgoing.target_host") == False):
                    self.status = status.STOPPED
                    print "exiting"
                    return self.status

            if self.status == status.STOPPED:
                return self.status
      
            # Get a list of items, either files or directories
            items = self.listDataDir()
            
            if items:
                self.info("Found a list of items to transfer of length '%d', starting with: %s" % (len(items), items[:3]))

            # completion condition is that we have seen the completion
            # file, and the data_stream directory is currently empty
            if (not items) and had_completion_file:
                self.status = status.COMPLETE
                return self.status

            # Start a counter to check status after every 5 items
            icount = 1

            stat_diff = False
            for item in items:
                # Since we cannot guarantee that the file being placed in the incoming
                # directory is not still being written to we:
                #  - check size and last mod time
                #  - wait 2 seconds
                #  - check size and last mod time again

                if os.path.isdir(item) == True:
                    for dirname, dirnames, filenames in os.walk(item):
                        for filename in filenames:
                            pth = os.path.join(dirname, filename)
                            full_path = os.path.join(self.dataset_dir, item)
                            stat1 = (futils.getLastUpdatedTime(full_path), futils.getSize(full_path))
                            time.sleep(5)
                            stat2 = (futils.getLastUpdatedTime(full_path), futils.getSize(full_path))
                            if stat1 != stat2:
                                self.info("File is still writing so ignore: %s" % item)
                                stat_diff = True
                                continue
                else:
                    full_path = os.path.join(self.dataset_dir, item)
                    stat1 = (futils.getLastUpdatedTime(full_path), futils.getSize(full_path))
                    time.sleep(5)
                    stat2 = (futils.getLastUpdatedTime(full_path), futils.getSize(full_path))

                if stat1 != stat2 or stat_diff == True:
                    self.info("File is still writing so ignore: %s" % item)
                    continue

                # Every fifth item, test status has not been changed or stopped
                if (icount % 5) == 0:
                    self.updateStatusAndConfig()
                    if self.status == status.STOPPED:
                        return self.status

                if self.doIgnore(item):
                    continue

                # Copy the item to remote host.
                # don't actually do anything with the return code. as
                # currently coded, TUC will already have logged an error /
                # quarantined the files as necessary
                tresp = tbc.transfer(item)

                if tresp != None and str(tresp.code) == "Failure":
                    if tresp.msg.find("Not all variables in") != -1:
                        # this data_stream will not continue as not all variables have been set
                        # exit cleanly
                        self.status = status.STOPPED
                        return self.status

                if item == self.completion_file:
                    had_completion_file = True

                icount += 1
            self.info("Sleeping for %d seconds..." % self.poll_interval)
            time.sleep(self.poll_interval)
            # if we get here - then all the files have been processed
            # if we are running oneoff then exit here
            if self.dconfig.get("global.oneoff") == True:
                runLoop = False
                # send a signal back to StagerController syaing that this
                # data_stream has completed
                os.kill(os.getppid(), signal.SIGUSR2)


    def doIgnore(self, item):
        """
        items to ignore in data_stream directory
        """
        full_path = self.getPathInDataDir(item)
        if full_path == self.quarantine_dir:
            return True

        # everything else to ignore is a dot file
        # we should already have filtered these out, but
        # to be safe:
        if item.startswith("."):
            return True

        return False
      

    def tidyDatasetDir(self):
        """
        Called on re-start.
        Remove any old control files lying around in the data_stream directory.
        NB it doesn't try to remove any other dotfiles (FIXME: should it?)
        """
        items = self.listDataDir(include_dotfiles = True)
        ctl_extn = self.dconfig.get("outgoing.control_file_extension")

        if ctl_extn:
            ctl_suffix = "." + ctl_extn
            for item in items:
                if item.endswith(ctl_suffix):
                    path = self.getPathInDataDir(item)
                    self.deleteOrWarn(path)


if __name__ == '__main__':

    from TestConfig import dc_mytest as dc
    dc["logging"]["log_level"] = "DEBUG"

    dtc = DatasetTransferController(dc)

    print dtc.processTransfers()
