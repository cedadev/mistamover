# BSD Licence                                                                                                 
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)                                          
# All rights reserved.                                                                                        
#                                                                                                             
# See the LICENSE file in the source distribution of this software for                                        
# the full license text.                                                                                      

import sys, os

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "unittests":
    raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "../lib")           
sys.path.append(lib_dir)

import ThankyouFile

if __name__ == '__main__':

    import os

    def test_thankyou():
        fname = "myfile.tmp"
        os.system("rm -f %s" % fname)

        a1 = ThankyouFile.ThankyouFile(fname)
        a1.create("foo")
        os.system("cat %s" % fname)
        a2 = ThankyouFile.ThankyouFile(fname)
        print a2.read()

    if len(sys.argv) == 2:
        if sys.argv[1] == "--thankyou":
            test_thankyou()
