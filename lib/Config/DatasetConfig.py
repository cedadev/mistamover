# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os

from BaseConfig import BaseConfig
import GlobalConfig
from StatusFlag import status

class DatasetConfig(BaseConfig):
    """
    A configuration which bases the filename on the global configuration, and
    inherits from the global configuration any variables which
    it does not provide locally.

    It also adds the substitution {{dataset_name}}
    """

    def __init__(self, dataset_name, gconfig, global_path = None, **kwargs):

        # allow a filename for gconfig
        if isinstance(gconfig, str):
            gconfig = GlobalConfig.GlobalConfig(gconfig)

        if gconfig["global"].has_key("dataset_config_dir"):
            gconfig["global"]["config_dir"] = gconfig["global"]["dataset_config_dir"]
            print "Re-setting '%s' to use configs in alternative dir: %s" % (dataset_name, gconfig["global"]["config_dir"])
            #print "PID: %s" % os.getpid()
  
        if global_path == None:
            file_path = os.path.join(gconfig["global"]["config_dir"], "dataset_%s.ini" % dataset_name)
        else:
            file_path = global_path
        self.name = dataset_name
        self.gconfig = gconfig
        BaseConfig.__init__(self, file_path, **kwargs)

    def mungeVars(self):
        """
        Further manipulation of specific variables beyond what's in the config
        """
        dset_sect = self["dataset"]
        incoming_sect = self["incoming"]
        outgoing_sect = self["outgoing"]
    
        if not dset_sect["directory"]:
            dset_sect["directory"] = os.path.join(self["global"]["base_data_dir"], self.name)

        if not incoming_sect["directory"]:
            incoming_sect["directory"] = os.path.join(self["global"]["base_incoming_dir"], self.name)

        if not outgoing_sect["quarantine_dir"]:
            outgoing_sect["quarantine_dir"] = os.path.join(
                dset_sect["directory"], "quarantine")

        status_str = dset_sect["status"]
        try:
            dset_sect["status"] = getattr(status, status_str.upper())
        except AttributeError:
            # default
            dset_sect["status"] = status.RUNNING

    def reread(self, reread_global = True):
        """
        Unconditionally reread the config file.        
        """
        if reread_global:
            self.gconfig.reread()

        BaseConfig.reread(self)
        self.copyVarsFromGlobal()
        self.mungeVars()

    def rereadIfUpdated(self):
        """
        Reread the config file if it or the 
        global config file has updated
        (later modification time than last read)
        """
        if self.gconfig.rereadIfUpdated():
            # global config has changed - need to remake regardless
            self.reread(reread_global = False)
            return True
        else:
            return BaseConfig.rereadIfUpdated(self)

    def copyVarsFromGlobal(self):
        """
        For any variables defined in the global config but not 
        defined locally in the dataset config file, copy them across
        """
        gconfig = self.gconfig
        for section in gconfig.keys():
            sect_global = gconfig[section]
            sect_dset = self[section]
            for k in sect_global.keys():
                if k not in sect_dset:
                    sect_dset[k] = sect_global[k]
      
    # FIXME: add compulsoryVars - see BaseConfig, and see GlobalConfig for example

if __name__ == '__main__':
    #import time
    from TestConfig import dc_mytest as dc
    dc.dump()
    #time.sleep(5)
    #dc.reread()
    #dc.dump()
