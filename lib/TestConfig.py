# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Import this for testing only.

Used in __name__ == '__main__' sections of various modules.
"""

import os

from Config import GlobalConfig
from Config import DatasetConfig
  
os.environ["CONFIG__global__top"] = ".."

gc = GlobalConfig("../conf/global.ini")
dc = DatasetConfig("hadgem2_2xco2", gc)

dc_mytest = DatasetConfig("mytest", gc)
