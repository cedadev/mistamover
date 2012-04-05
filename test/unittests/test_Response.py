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

import Response

if __name__ == '__main__':
    def test_response():
        fail1 = Response.Response(Response.failure, "angst1")
        fail2 = Response.failure("angst2")
        succ1 = Response.Response(Response.success, "happiness1")
        succ2 = Response.success("happiness2")

        print Response.success, Response.failure, Response.success(), Response.failure()

        print fail1, fail2, succ1, succ2
        if fail1:
            print "should not get here"
        if succ1:
            print "should get here"

        print fail1 + fail2
        print fail1 + succ2
        print succ1 + fail2
        print succ1 + succ2

    if len(sys.argv) == 2:
        if sys.argv[1] == "--response":
            test_response() 
