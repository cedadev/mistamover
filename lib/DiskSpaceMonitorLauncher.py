# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os

from FileUtils import futils
import Daemon
import DiskSpaceMonitor

class DiskSpaceMonitorLauncher(object):

    """
    A launcher which starts and stops different DiskSpaceMonitor daemons
    for each filesystem on which data_stream directories live.  Note that
    it doesn't test which filesystem incoming directories live on; 
    these are assumed to be on the same filesystem as the data_stream 
    directory for that data_stream.
    """

    def __init__(self, gconfig, dconfigs, logger = None):
        """
        Inputs:  gconfig  - GlobalConfig object
                 dconfigs - list of DatasetConfig objects
                 logger (optional) - client logger object
        """
        self.gconfig = gconfig
        self.dconfigs = dconfigs
        self.logger = logger
        self.groups = self.groupDatasetsByDisk()
        self.daemons = {}
        self.tags = []
        if logger:
            logger.debug("DSML init")

    def launch(self):
        """
        Launch all the DiskSpaceMonitor daemons that are required
        """
        for filesys in self.groups:
            daemon = self.launchOne(filesys, self.groups[filesys])
            self.daemons[filesys] = daemon


    def launchOne(self, ds_filesys, ds_group):
        """
        launch a single DiskSpaceMonitor for a group of data_stream
        that reside on a given filesystem.

        inputs:  ds_filesys (string) - name of mount point
                 ds_group - list of DatasetConfig objects just for 
                              this group of data_streams
        """
        desc_short, desc_long = self.getDescription(ds_filesys)
        desc_short = self.makeUnique(desc_short)
        if self.logger:
            self.logger.info("starting %s" % desc_long)
        daemon = Daemon.DaemonCtl(DiskSpaceMonitor.DiskSpaceMonitor,
                                  args = [ds_filesys, self.gconfig, ds_group,
                                          desc_short, desc_long],
                                  description = "mistamover_" + desc_short)
        daemon.desc_long = desc_long
        return daemon


    def makeUnique(self, tag):
        """
        Given a tag, append prefixes as required so that it is unique.
        Reason for this is so that if more than one filesystem has the same
        short name (last pathname element of the mount point), they will have
        distinct tags for logging and process naming purposes.
        """
        n = 1
        tag_stem = tag
        while tag in self.tags:
            tag = "%s%s" % (tag_stem, n)
            n += 1
        self.tags.append(tag)
        return tag


    def kill(self):
        """
        Kill all DiskSpaceMonitor daemons that have been launched
        """
        m = self.daemons
        for filesys in m:
            daemon = m[filesys]
            self.killOne(daemon)
        self.daemons = {}


    def killOne(self, daemon):
        """
        Kill one daemon.  Argument is a DaemonCtl object.
        """
        if self.logger:
            self.logger.info("stopping %s" % daemon.desc_long)
        daemon.shutdown()
        


    def groupDatasetsByDisk(self):
        """
        Return a dictionary containing the data_streams for each file system:
        key is the mount point, value is an array of data_stream config 
        objects.  Use this so that we can launch a separate DiskSpaceMonitor 
        for each filesystem.
        """
        ds_groups = {}
        for dconfig in self.dconfigs.values():
            ds_dir = dconfig.get("data_stream.directory");
            filesys = futils.getMountPointForPath(ds_dir)
            if filesys not in ds_groups:
                ds_groups[filesys] = []
            ds_groups[filesys].append(dconfig)
        return ds_groups


    def getDescription(self, filesys):
        """
        Get short and long descriptions for a given filesystem
        (input string is name of the mount point)
        long to be used for log messages + emails
        short to be used for tags on log messages and for process naming
        """
        if filesys == None:
            dshort = "dsm"
            dlong = "disk space monitor"
        else:
            # use the last part of the mount point name for a short 
            # label for the process (most likely to be unique)
            dshort = "dsm_%s" % (os.path.basename(filesys) or "/")
            dlong = "disk space monitor for filesystem %s" % filesys
        return (dshort, dlong)


if __name__ == '__main__':
    import time
    import MiStaMoverController

    os.environ["CONFIG__global__top"] = ".."
    s = MiStaMoverController.MiStaMoverController("../conf/global.ini")

    dsml = DiskSpaceMonitorLauncher(s.gconfig, s.dconfigs, logger = s.logger)

    dsml.launch()
    time.sleep(1)
    os.system("ps uxw | egrep 'mistamover|dsm'")
    time.sleep(600)
    dsml.kill()
