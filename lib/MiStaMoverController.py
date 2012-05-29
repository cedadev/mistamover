# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os
import stat
import string
import sys
import time
import signal

import Daemon
from Config import GlobalConfig
from Config import DatasetConfig
import DatasetTransferController 
import DatasetArrivalMonitor
import LoggerServer
import LoggerClient
import DiskSpaceMonitorLauncher

class MiStaMoverController(object):
    """
    This is the daemon process that manages a group of other class 
    instances which are run in sub-processes, specifically:

      * one LoggerServer

      * one DiskSpaceMonitor for each filesystem 
           (via DiskSpaceMonitorLauncher)

      * a DatasetTransferController for each data_stream

      * a DatasetArrivalMonitor for each data_stream which needs it

    It is the top-level in MiStaMover (apart from the main program MiStaMover.py
    which basically just sets a few variables and calls this)
    """  

    def __init__(self, global_config_path, debug_on=False, oneoff=False):
        """
        Reads global config file
        """
        self.oneoff = oneoff
        self.global_config_path = global_config_path
        self.readConfig(global_config_path)

        if self.oneoff == True:
            if len(self.datasets) != 1:
                print "in oneoff mode - only a single data_stream can be transfered at a time"
                sys.exit()

        #self.gconfig.dump()
        if self.gconfig.checkSet("global.debug_on"):
            self.debug_on = self.gconfig.get("global.debug_on")
        else:
            self.debug_on = debug_on

        # set up some default values
        if not self.gconfig.checkSet("logging.base_log_dir"):
            if self.gconfig.checkSet("global.top"):
                gtop = self.gconfig.get("global.top")
                self.gconfig.set("logging.base_log_dir", gtop + "/log")

        if not self.gconfig.checkSet("global.base_data_dir"):
            if self.gconfig.checkSet("global.top"):
                gtop = self.gconfig.get("global.top")
                self.gconfig.set("base.base_data_dir", gtop + "/data")

        self.checkConfig()

        self.sub_procs = {}

        if not os.path.exists(self.gconfig.get("logging.base_log_dir")):
            print ("log path " + self.gconfig.get("logging.base_log_dir") + 
                " does not exist")
            sys.exit()

        self.initLogger()

        # jah
        # this seems to be necessary otherwise signals dont seem to be caught
        signal.signal(signal.SIGINT, self.stopHandler)
        signal.signal(signal.SIGTERM, self.stopHandler)
        signal.signal(signal.SIGUSR2, self.stopHandler)        

    def checkConfig(self):
      if (self.gconfig.checkSet("global.top") == False):
          raise Exception("global.top must be set")
      if (self.gconfig.checkSet("global.data_stream_config_dir") == False and
          self.gconfig.checkSet("global.config_dir") == False):
          raise Exception("either global.data_stream_config_dir OR global.config_dir must be set")
      if (self.gconfig.checkSet("global.general_poll_interval") == False):
          raise Exception("global.general_poll_interval must be set")
      if (self.gconfig.checkSet("logging.base_log_dir") == False):
          raise Exception("logging.base_log_dir must be set")
      if (self.gconfig.checkSet("logging.log_level") == False):
          raise Exception("logging.log_level must be set")
      if (self.gconfig.checkSet("logging.port") == False):
          raise Exception("logging.port must be set")
      if (self.gconfig.checkSet("email.threshold") == False):
          raise Exception("email.threshold must be set")
      if (self.gconfig.checkSet("email.from") == False):
          raise Exception("email.from must be set")
      if (self.gconfig.checkSet("email.recipient") == False):
          raise Exception("email.recipient must be set")
      if (self.gconfig.checkSet("email.subject") == False):
          raise Exception("email.subject must be set")
      if (self.gconfig.checkSet("email.smarthost") == False):
          raise Exception("email.smart must be set")
      if (self.gconfig.checkSet("disk_space_monitor.poll_interval") == False):
          raise Exception("disk_space_monitor.poll_interval must be set")
      if (self.gconfig.checkSet("disk_space_monitor.base_priority") == False):
          raise Exception("disk_space_monitor.base_priority must be set")

    def dumpConfig(self):
        self.gconfig.dump()
        for d in self.dconfigs.values():
            d.dump()

    def main(self):
        """
        Main loop.
        Start the daemons, then wait until we are told to stop.
        It checks the data_stream config directory for new data_streams if that
        method is used.
        """

        self.startAll()
        self.stopRequested = False
        for signo in (signal.SIGTERM, signal.SIGINT):
            signal.signal(signo, self.stopHandler)
        
        while not self.stopRequested:
            # any signal will cause sleep to terminate early
            # after 30 seconds test for changes to configs dir
            time.sleep(30)
            self.scanDatasetConfigsForChange()
    
        self.stopAll()
                


    def stopHandler(self, signo, frame):
        """
        A signal handler that just records that we were signalled.
        Doesn't bother to see what signal we were called with, as
        should only be installed as a handler for appropriate signals.
        """
        if self.logger:
            self.info("Received signal %s" % signo)
        if signo != signal.SIGUSR2:
            self.stopRequested = True
            self.stopAll()
        else:
            print "sigusr1 was handled"
            totalDataSetsRunning = 0
            for k in self.sub_procs:
                print k
                v = self.sub_procs[k]
                # d is a daemonCtl instance
                d = v['sender']
                time.sleep(0.1)
                if d.isRunning():
                    totalDataSetsRunning += 1
            if totalDataSetsRunning == 0:
                print "no data_streams seem to be running"
                self.stopRequested = True
                self.stopAll()

    def readConfig(self, global_config_path):
        """
        Read global config and dictionary of all the data_stream configs.
        """
        self.gconfig = GlobalConfig(global_config_path)
        self.global_config_path = global_config_path

        # check that we can access various directories
        if not os.access(self.gconfig.get("global.config_dir"), os.R_OK):
            print "unable to access global.config_dir " + \
                str(self.gconfig.get("global.config_dir"))
            sys.exit()
        if not os.access(self.gconfig.get("global.base_incoming_dir"), os.R_OK):
            print "unable to access global.base_incoming_dir " + \
                str(self.gconfig.get("global.base_incoming_dir"))
            sys.exit()
        if not os.access(self.gconfig.get("global.top"), os.R_OK):
            print "unable to access global.top " + \
                str(self.gconfig.get("global.top"))
            sys.exit()
        if not os.access(self.gconfig.get("global.base_data_dir"), os.R_OK):
            print "unable to access global.base_data_dir " + \
                str(self.gconfig.get("global.base_data_dir"))
            sys.exit()        


        # Decide which dataset listing method to use:
        #  1. ``data_stream_config_dir`` implies get all found in that directory
        #  2. ``data_stream_list`` implies picking up only those in the directory listed

        if self.gconfig["global"].has_key("data_stream_config_dir"):
            self.gconfig["global"]["config_dir"] = self.gconfig["global"]["data_stream_config_dir"]
            self._populateDatasetConfigsFromConfigDir()
            print ("Using data_streams in alternative dir: %s" % 
                self.gconfig["global"]["config_dir"])
            print "Using data_streams: %s" % self.datasets
        else:
            self.datasets = string.split(self.gconfig["global"]["data_stream_list"])

        if len(self.datasets) == 0:
            print "WARNING: No data_stream configuration files found!?! Stopping MiStaMover!"
            sys.exit()

        self.dconfigs = {}
        self._loadDatasetConfigs()

    def _loadDatasetConfigs(self):
        """
        Goes through and loads up data_stream configs if not already there. 
        Returns a list of those data_streams that have just been added.
        """

        ds_added = []  

        for ds_name in self.datasets:
            data_stream_path = self.gconfig.get("global.config_dir")
            # check that the config files have 400 permissions
            ds_filepath = data_stream_path + "/ds_" + ds_name + ".ini"
            st = os.stat(ds_filepath).st_mode
            rv = stat.S_IMODE(st)
            if rv == stat.S_IRUSR:
                if ds_name not in self.dconfigs.keys():
                    if self.oneoff == False:
                        self.dconfigs[ds_name] = DatasetConfig(ds_name, self.gconfig)
                    else:
                        self.dconfigs[ds_name] = (DatasetConfig(ds_name, self.gconfig,
                            self.global_config_path))
                    ds_added.append(ds_name)

                # Now they should all have been loaded. When re-trying, try all those
                # that are STOPPED as they might have been re-started
                ds_status = self.dconfigs[ds_name].get("data_stream.status")

                if ds_status == "<stopped>":
                    print "Re-scanning previously stopped data_stream just in case re-started: %s" % ds_name

                    self.dconfigs[ds_name] = \
                        DatasetConfig(ds_name, self.gconfig)

                    new_ds_status = self.dconfigs[ds_name].get("data_stream.status")
                    if new_ds_status == "<running>":
                        ds_added.append(ds_name)
            else:
                print ds_filepath + " must have permissions of 400"
                if hasattr(self, 'info'):
                    self.info("%s must have permissions of 400" % ds_filepath)
                # remove the offending item
                self.datasets.remove(ds_name)
        return ds_added


    def _removeDeletedDatasets(self):
        """
        Remove any (and try stopping the sub-process) data_streams that have 
        disappeared from the configuration.
        """
        for ds_name in self.dconfigs.keys():

            if ds_name not in self.datasets:
                (self.info("STOPPING data_stream because removed from data_stream list: %s" %
                    ds_name))
                self.stopDatasetProcs(ds_name) 
                del self.dconfigs[ds_name]


    def _populateDatasetConfigsFromConfigDir(self):
        """
        Lists all files in ``data_stream_config_dir`` to generate a list of 
        data_streams to use. Stores them in ``self.data_streams``.
        """

        if self.gconfig["global"].has_key("data_stream_config_dir"):
            self.gconfig["global"]["config_dir"] = self.gconfig["global"]["data_stream_config_dir"]
            dataset_config_dir = self.gconfig.get("global.config_dir")

            print ("Scanning data_stream configs dir for new data streams: %s" % 
                dataset_config_dir)
            dataset_config_files = ([conf_file for conf_file in 
                os.listdir(dataset_config_dir) if conf_file[0] != "."])
            self.datasets = ([i.replace("dataset_", "").replace(".ini", "") 
                for i in dataset_config_files])
        else:
            pass


    def scanDatasetConfigsForChange(self):
        """
        Reads ``data_stream_config`` dir and reacts to any new config files or 
        any deletions.
        """
        self.gconfig = GlobalConfig(self.global_config_path)
        self.datasets = string.split(self.gconfig.get("global.data_stream_list"))

        ds_added = self._loadDatasetConfigs()        

        print "Scanning for new data_stream configs or updated status in existing configs..."

        # Now start up those that have just been added
        for ds_name in ds_added:
            print "Starting procs for data_stream %s" % ds_name
            self.info("starting procs for data_stream %s" % ds_name)
            self.startDatasetProcs(ds_name) 
           
        # And remove any that have been deleted 
        self._removeDeletedDatasets()

        
    def startAll(self):
        """
        Starts up sub-processes: log server, disk space monitor, 
          and data_stream specific processes
        """
        self.startLogServer()

        self.dsml = DiskSpaceMonitorLauncher.DiskSpaceMonitorLauncher(
            self.gconfig, self.dconfigs, logger = self.logger)
        self.dsml.launch()

        self.info("started log server")
        for ds_name in self.datasets:
            self.info("starting procs for data_stream %s" % ds_name)
            self.startDatasetProcs(ds_name)


    def stopAll(self):
        """
        Stop the same things that startAll() starts
        """
        for ds_name in self.datasets:
            self.info("signalling procs for data_stream %s to stop" %
                             ds_name)
            self.stopDatasetProcs(ds_name)
        for ds_name in self.datasets:
            self.info("waiting for procs for data_stream %s to stop" %
                             ds_name)
            self.waitForDatasetProcs(ds_name)

        # stop disk space monitor
        try:
            self.dsml.kill()
        except Exception:
            pass 
        self.stopLogServer()

        for k in self.sub_procs:
            v = self.sub_procs[k]
            for j in v:
                q = v[j]
                try:
                    os.kill(q.pid, signal.SIGUSR1)
                except:
                    pass
            
    def waitForDatasetProcs(self, ds_name):
        """
        Wait for processes associated with a named data_stream to stop
        """
        daemons = self.getDatasetProcs(ds_name)
        for d in daemons:
            if d.isRunning():
                status = d.getStatus(wait = True)
                self.info("process '%s' exited with status %s" % \
                                 (d.description, status))


    def initLogger(self):
        """
        initialise the logger client object for logging from this module.
        NB this is completely separate from the server side, which is also 
        started by MiStaMoverController
        """
        self.logger = LoggerClient.LoggerClient(
            self.gconfig,
            tag = "MiStaMover_ctl",
            name = "top-level MiStaMover controller",
            debug_on = self.debug_on)
        self.logger.exportMethods(self)

        
    def startLogServer(self):
        """
        Start the logger server process
        """
        self.log_server_proc = Daemon.DaemonCtl(self.runLogger,
                                                args = [self.gconfig],
                                                description = "MiStaMover_log_server")
        
    def stopLogServer(self):
        try:
            self.log_server_proc.shutdown()
        except Exception, ex:
            str(ex)
        

    def runLogger(self, gconfig):
        """
        This is method that is run in the daemon when startLogServer()
        is called.

        Don't call this directly unless you want it running
        in the foreground.
        """
        server = LoggerServer.LoggerServer(self.gconfig)
        server.serve()


    def startDatasetProcs(self, ds_name):
        """
        Sets up the data_stream sub-process.

        Note that if the source_requires_checksum argument is set to True in
        the config file then we need to set up two sub-processes:

        1. to monitor arrivals, run checksums and produce checksum files
        (to confirm receipt).
        2. to send data on.
        In other cases we only set up the second sub-process.
        """
        self.info("starting Transfer Controller for data_stream %s"
                         % ds_name)

        dconfig = self.dconfigs[ds_name]

        proc_misc = []

        if dconfig.get("outgoing.transfer_protocol") != "none":
            proc_misc.append((self.runDatasetTransferController,
                              "transfer controller", "dtc_", "sender"))
        
        if dconfig['incoming']['require_arrival_monitor']:
        #if dconfig.get("incoming.require_arrival_monitor") == "True":
            proc_misc.append((self.runDatasetArrivalMonitor,
                              "arrival monitor", "dam_", 
                              "arrival_monitor"))

        sub_procs = {}
        
        for method, descrip, short_desc, key in proc_misc:
            full_descrip = "%s for data_stream %s" % (descrip, ds_name)
            self.info("starting %s" % full_descrip)           
            daemon = Daemon.DaemonCtl(method,
                                      args = [dconfig],
                                      description = "MiStaMover_" + short_desc + ds_name)
            sub_procs[key] = daemon
        self.sub_procs[ds_name] = sub_procs


    def runDatasetTransferController(self, *args):
        """
        This is method that is run in the daemon when startLogServer()
        is called.

        Don't call this directly unless you want it running
        in the foreground.
        """       
        dconfig = args[0]
        # set up a config item so that we can do oneoff etc
        dconfig.set("global.oneoff", self.oneoff)
        dtc = (DatasetTransferController.DatasetTransferController(dconfig, 
            debug_on=self.debug_on))
        return dtc.processTransfers()

    
    def runDatasetArrivalMonitor(self, *args):#dconfig):
        """
        This is a method that is run in a daemon when startDatasetProcs()
        is called.

        Don't call this directly unless you want it running
        in the foreground.
        """
        dconfig = args[0]
        dam = DatasetArrivalMonitor.DatasetArrivalMonitor(dconfig)
        return dam.monitor()


    def getDatasetProcs(self, ds_name):
        """
        This is a method that is run in a daemon when startDatasetProcs()
        is called.

        Don't call this directly unless you want it running
        in the foreground.
        """
        daemons = []
        try:
            proc_dict = self.sub_procs[ds_name]
            daemons.append(proc_dict["sender"])
            daemons.append(proc_dict["arrival_monitor"])
        except KeyError:
            pass
        return daemons


    def stopDatasetProcs(self, ds_name, cleanly=True): 
        """
        Stops a data_stream sub-process by sending a signal to the sub-process
        requesting it to stop after the current transfer.
        """
        daemons = self.getDatasetProcs(ds_name)
        
        for d in daemons:
            if cleanly:
                d.sendSignal("USR1")
            else:
                d.shutdown()

        
if __name__ == '__main__':
    os.environ["CONFIG__global__top"] = ".."

    if len(sys.argv) == 2:
        print sys.argv
        if sys.argv[1] == "--checkConfig":
            s = MiStaMoverController("../conf/global.ini")
            s.checkConfig()
        if sys.argv[1] == "--dumpConfig":
            s = MiStaMoverController("../conf/global.ini")
            s.dumpConfig()
        if sys.argv[1] == "--startStager":
            s = MiStaMoverController("../conf/global.ini")
            s.main()
