# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
A disk space monitor

See doc string for class DiskSpaceMonitor for details
"""

import os
import time
import tempfile

from FileUtils import futils

import LoggerClient
from Config import GlobalConfig
from Config import DatasetConfig

class DiskState(object):
    # note - the numerical values are arbitrary but the 
    # ordering of them matters
    GOOD = 4  # restart transfers if previously stopped
    OKAY = 3  # allow transfers if not stopped, but do not restart
    LOW = 2   # stop transfers of low prio dsets
    VLOW = 1  # delete files


class DiskSpaceMonitor(object):

    """
    A disk space monitor.

    Monitors the disk space in a given set of data_stream directories,
    and applies three thresholds:

        - fall below low disk space threshold:
            stop arrival of all data_streams which are of priority <= base
            priority

        - below very low disk space threshold:
            Delete transfer units from data_streams starting from the lowest
            priority, until back above this threshold.  Apply to data_streams with
            increasing priority as necessary, but only as far as the base
            priority.  If still below this threshold, then stop high-priority
            (> base priority) data_streams but do not delete transfer units
            from them.

        - rise above low disk threshold:
            restart arrival of high priority (> base prio) data_streams

        - rise above good disk threshold:
            restart arrival of all data_streams
            
    """

    def __init__(self, filesys, gconfig, dconfigs,
                 desc_short = "dsm",
                 desc_long = "disk space monitor", 
                 debug_on = False):
        """
        filesys (string) is the name of the filesystem being monitored.
        (In fact it will work if it is any directory on that filesystem, 
        but in practice the calling code will pass the actual mount point.)

        gconfig should be a single GlobalConfig object

        dconfigs should be an array of DatasetConfig objects
        """
        self.filesys = filesys
        self.gconfig = gconfig
        self.dconfigs = dconfigs
        self.config = gconfig["disk_space_monitor"]  # for convenience
        self.poll_interval = (self.config["poll_interval"] 
                              or gconfig["global"]["general_poll_interval"])

        self.base_prio = self.config["base_priority"]

        self.prio_sect = 'data_stream'
        self.prio_item = 'priority'
        self.stop_file_name = gconfig["incoming"]["stop_file"]

        if self.gconfig.checkSet("global.debug_on"):
            self.debug_on = self.gconfig.get("global.debug_on")
        else:
            self.debug_on = debug_on
        self.initLogger(desc_short, desc_long)

        # sort configs by priority
        self.applyDefaultPriorities()
        self.dconfigs.sort(self.cmpByPrio)

        for dc in self.dconfigs:
            self.debug("Dataset %s priority %s" % (dc.name, 
                                                   self.getPriority(dc)))

        self.monitor()  # enter main loop


    def initLogger(self, desc_short, desc_long):
        """
        Initialise the logger client module
        """
        self.logger = LoggerClient.LoggerClient(self.gconfig, 
                                                tag = desc_short,
                                                name = desc_long)
        # import some methods from the logger
        self.logger.exportMethods(self)

        self.info("startup")        


    def diskStateTransition(self, threshold, state, prev_state, direction):
        """
        Test for transition to specified disk state in specified 
        direction (1 for rising (improving), -1 for falling (worsening)).
        Also true if the current state is on the right side of the 
        threshold and it is the first iteration (prev_state == None).
        """
        cmp1 = cmp(state, threshold)
        if not (cmp1 == 0 or cmp1 == direction):
            return False

        if prev_state == None:
            return True

        cmp2 = cmp(threshold, prev_state)
        return (cmp2 == direction)


    def monitor(self):
        """
        The main loop
        """
        prev = None

        while True:
            state = self.getDiskState()
            self.debug("disk space state on %s: %s" % 
                       (self.filesys, state))

            if self.diskStateTransition(DiskState.GOOD, state, prev, 1):
                self.restartAllDatasets()

            if self.diskStateTransition(DiskState.OKAY, state, prev, 1):
                self.restartHighPriorityDatasets()

            if self.diskStateTransition(DiskState.LOW, state, prev, -1):
                self.stopDatasetsExceptHighPrio()

            # drasticAction called on every iteration if in VLOW state, not
            # just on state transition, so that it can keep deleting files
            # if more somehow arrive
            if (state == DiskState.VLOW):
                self.drasticAction()
                  
            time.sleep(self.poll_interval)
            prev = state


    def restartAllDatasets(self):
        """
        Remove .stop files for all data_streams
        """
        self.info("restartAllDatasets called")
        for dc in self.dconfigs:
            self.removeStopFile(dc)


    def restartHighPriorityDatasets(self):
        """
        Remove .stop files for data_streams whose priorities exceed the
        base priority
        """
        self.info("restartHighPriorityDatasets called")
        for dc in self.dconfigs:
            if self.getPriority(dc) > self.base_prio:
                self.removeStopFile(dc)


    def stopDatasetsExceptHighPrio(self):
        """
        Create .stop files for data_streams whose priorities do not exceed the
        base priority
        """
        self.info("stopDatasetsExceptHighPrio called")
        for dc in self.dconfigs:
            if self.getPriority(dc) <= self.base_prio:
                self.createStopFile(dc)


    def drasticAction(self):
        """
        Delete files from low or base priority data_streams if necessary,
        until disk space is no longer VLOW, 
        and if still necessary then also stop high priority data_streams,
        """
        self.info("drasticAction called")

        deletions = []

        for dc in self.dconfigs:

            if self.getPriority(dc) <= self.base_prio:
                # stop file should already have been created,
                # but this is cheap, so repeat for good measure
                self.createStopFile(dc)
                if dc.checkSet("data_stream.deletion_enabled"):
                    if dc.get("data_stream.deletion_enabled") == True:
                        deleted_enough = \
                            self.deleteFilesWhileVeryLowDisk(
                                dc, deletions)

                        if deleted_enough:
                            break
                    else:
                        self.info("not deleting files - but need more disk space!")
                
        else:
            # deletions of items from low priority data_streams didn't fix
            # the problem, so stop all arrivals
            for dc in self.dconfigs:
                self.createStopFile(dc)
            self.error("Had to stop all arrivals")

        if deletions:
            self.error("Had to delete files: %s" % deletions)


    def getTUsForDeletion(self, dconfig):
        """
        Get list of candidate transfer units for deletion, in order,
        for a data_streams (argument is a DatasetConfig object)
        
        Looks in: arrivals directory (if there is one), 
        data_stream directory and quarantine directory.

        First sort key is that it does arrivals dir before anything else, as
        this reduces checksumming.  Apart from that, it does most recently
        created files first as these are the likely to be the easiest to find
        another copy. (NB uses change time, as this will more accurately
        reflect when it was really created on THIS system, whereas mtime can
        be set by rsync to match the modification time on another system)
        """

        ds_dir = dconfig["data_stream"]["directory"]
        q_dir = dconfig["outgoing"]["quarantine_dir"]
        arr_dir = dconfig["incoming"]["directory"]

        list_dir_func = lambda dir_path: \
                           futils.listDir(dir_path, 
                                          fullPaths = True,
                                          emptyListOnException = True)

        # add items in dataset dir
        transfer_units = list_dir_func(ds_dir)

        if q_dir:
            # if there is a quarantine directory, add items in the quarantine
            # directory, but first exclude the quarantine dir itself, which
            # may be an entry under the dataset dir
            transfer_units = filter(lambda path: path != q_dir,
                                    transfer_units) \
                               + list_dir_func(q_dir)
        
        
        transfer_units.sort(key = futils.getCtimeOrNone,
                            reverse = True)
        
        # add items in arrivals dir at start (if there is one)
        if arr_dir:
            arr_transfer_units = list_dir_func(arr_dir)
            arr_transfer_units.sort(key = futils.getCtimeOrNone,
                                    reverse = True)
            transfer_units = arr_transfer_units + transfer_units

        # Okay we're done, though for good measure check they all really 
        # exist
        transfer_units = filter(os.path.exists, transfer_units)

        return transfer_units


    def deleteFilesWhileVeryLowDisk(self, dconfig, deletions):
        """
        Keep deleting files from a data_stream while disk state is 
        very low.  Return a True/False value for whether a
        better (i.e. not VLOW) disk state was reached.

        dconfig is the DatasetConfig object
        'deletions' argument is an array provided by the caller;
          it will be appended to with pathnames deleted, so that
          the caller can log these
        """

        for tu_path in self.getTUsForDeletion(dconfig):

            # test disk space before deleting
            if self.getDiskState() != DiskState.VLOW:
                return True

            deletions.append(tu_path)
            if os.path.isdir(tu_path):
                # recursive deletion - may take a while, so 
                # move it inside a temporary dot-dir first (and then
                # delete from the level of the dot-dir itself) to
                # reduce chance of races with TransferUnitController 
                # trying to transfer it
                parent_dir = os.path.dirname(tu_path)
                del_dir = tempfile.mkdtemp(dir = parent_dir,
                                          prefix = ".del_tmp_")
                os.rename(tu_path, del_dir)
                status = futils.deleteDir(del_dir)
            else:
                status = futils.deleteFile(tu_path)
            if not status:
                self.warn("could not delete %s: %s" % \
                              (tu_path, status))

        # repeat the test one final time (after last deletion)
        # to determine return value
        return (self.getDiskState() != DiskState.VLOW)

                
    def createStopFile(self, dconfig):
        """
        Create stop file for a given data_stream.
        """
        path = self.getStopFilePath(dconfig)
        if not os.path.exists(path):
            self.info("Creating stop file %s" % path)
            fh = open(path, "w")
            fh.close()


    def removeStopFile(self, dconfig):
        """
        Remove stop file for a given data_stream.
        """
        path = self.getStopFilePath(dconfig)
        if os.path.exists(path):
            self.info("Removing stop file %s" % path)
            os.remove(path)
    

    def getStopFilePath(self, dconfig):
        """
        Get the stop file path for a given data_stream.
        This will be in either the incoming directory (if there is an
        arrival monitor) or the data_stream directory (if there is not).
        """
        iconfig = dconfig["incoming"]
        if iconfig["require_arrival_monitor"]:
            stop_file_dir = iconfig["directory"]
        else:
            stop_file_dir = dconfig["data_stream"]["directory"]

        # could conceivably need to create this, if for a new dataset 
        # this gets there before the TransferUnitController does
        futils.ensureDirExists(stop_file_dir)

        stop_file_path = os.path.join(stop_file_dir, 
                                      self.stop_file_name)
        return stop_file_path


    def applyDefaultPriorities(self):
        """
        Set any unspecified priorities to the base priority
        """
        for dconfig in self.dconfigs:
            if self.getPriority(dconfig) == None:
                self.setPriority(dconfig, self.base_prio)
                

    def getPriority(self, dconfig):
        """
        Get priority level for a data_stream
        """
        return dconfig[self.prio_sect][self.prio_item]


    def setPriority(self, dconfig, value):
        """
        Set priority level for a data_stream
        (in memory; does not alter config file)
        """
        dconfig[self.prio_sect][self.prio_item] = value


    def cmpByPrio(self, dconfig1, dconfig2):
        """
        Return ordering of two data_streams by priorities.
        Falls back to comparing names in event of equal prioirities, 
        for sake of a definite ordering.
        (NB sort using this function will return list in increasing order,
        i.e. lowest priority first.)
        """
        return (cmp(self.getPriority(dconfig1), self.getPriority(dconfig2))
                or cmp(dconfig1.name, dconfig2.name))


    def getDiskState(self):
        """
        Returns a symbolic token representing the disk state
        """
        total, free = futils.getDiskSpace(self.filesys,
                                          getNonRoot=True)
        free /= 1024.  # KB -> MB
        self.debug("%f MB" % free)
        if free > self.config["level_good"]:
            return DiskState.GOOD
        if free < self.config["level_vlow"]:
            return DiskState.VLOW
        if free < self.config["level_low"]:
            return DiskState.LOW
        return DiskState.OKAY
