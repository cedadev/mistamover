# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from BaseConfig import BaseConfig

class GlobalConfig(BaseConfig):
    """
    A configuration-file object based on BaseConfig with the added feature of 
    some compulsory variables which are relevant to stager global configuration
    """

    def reread(self):
        BaseConfig.readDefaults(self)
        BaseConfig.reread(self)
        self.checkCompulsoryVars()

    # FIXME: expand this (compulsory vars for global config)
    #compulsoryVars =  (
    #    ("global", ["base_data_dir", "config_dir"]),
    #    ("outgoing", [("retry_count", int)]),
    #    ("logging", [("base_log_dir", str)]),
    #    )

if __name__ == '__main__':
    print "this should succeed:"
    gconfig = GlobalConfig("../conf/global.ini")

    print "this should fail:"
    gconfig2 = GlobalConfig("../conf/dataset_hadgem2_2xco2.ini")
  
  
