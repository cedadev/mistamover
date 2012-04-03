#!/usr/bin/env python
# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import getopt
import sys
import os

import runCommand
#import commands

class Gridftp:
    def parse_args(self, args):
        opts, pargs = getopt.getopt(args, "m:u:p:g:s:P:U:V")

        self.verify_transfers = False
        self.globus_location = '/opt/gt5.0.3'
        self.streams = 8
        self.port = 2811
        self.url_type = "ftp"

        for opt, val in opts:
            if opt == "-m":
                self.mode = val
            elif opt == "-u":
                self.username = val
            elif opt == "-p":
                self.read_password_file(val)
            elif opt == "-g":
                self.globus_location = val
            elif opt == "-s":
                self.streams = int(val)
            elif opt == "-P":
                self.port = int(val)
            elif opt == "-U":
                self.url_type = val
            elif opt == "-V":
                self.verify_transfers = True
            else:
                raise RuntimeError

        for key in 'username', 'password', 'mode':
            if not hasattr(self, key):
                raise ValueError("%s not set" % key)

        self.local_dir, self.remote_host, self.remote_dir = pargs[0:3]
        self.files = pargs[3:]

        os.environ["GLOBUS_LOCATION"] = self.globus_location


    def read_password_file(self, filename):
        f = open(filename)
        self.password = f.readline().replace("\n", "")
        f.close()
        

    def run_command(self, command, input="", get_stderr=False):
        status, output, error = runCommand.runCommand(command, input)
        # print "c='%s' i='%s'" % (command, input)
        # print "s='%s' o='%s' e='%s'" % (status, output, error)
        succ = (status / 256 == 0)
        if get_stderr:
            output += error
        return succ, output


    def do_transfer(self, file):

        if "/" in file:
            raise ValueError("file %s should be filename only" % file)

        exe = "%s/bin/globus-url-copy" % self.globus_location
    
        remote_url = "%s://%s:%s@%s:%s%s/%s" % \
            (self.url_type,
             self.username,
             self.password,
             self.remote_host,
             self.port, 
             self.remote_dir,
             file)
        
        local_url = "file://%s/%s" % (self.local_dir, file)

        url_pair = None
        if self.mode == 'get':
            url_pair = '"%s" "%s"' % (remote_url, local_url)
        elif self.mode == 'put':
            url_pair = '"%s" "%s"' % (local_url, remote_url)
        elif self.mode == 'test':
            dummy_url = "file:///**DUMMY**"
            command = ( exe,
                        "-do", "-",
                        "-sync", 
                        "-sync-level", "1" )

            input = '"%s" "%s"\n' % (remote_url, dummy_url)
            succ, output = self.run_command(command, input)
            exists = (succ and output != "")
            if exists:
                print "%s exists" % file
            else:
                print "%s does not exist" % file
            return exists

        if url_pair:
            command = ( exe,
                        "-p", "%s" % self.streams,
                        "-f", "-" )
            input = "%s\n" % url_pair
            succ, output = self.run_command(command, input)

            if succ and self.verify_transfers:
                # print "going to verify... press enter"
                # dummy = sys.stdin.readline()
                # print "going to verify... now"
                
                command2 = ( exe,
                             "-do", "-",
                             "-sync",
                             "-sync-level", "3",
                             "-f", "-")
                input = "%s\n" % url_pair
                # (above line redundant, included for clarity)

                succ2, output2 = self.run_command(command2, input, get_stderr=True)
                succ = succ2 and (output2 == "")

            if succ:
                print "copied %s" % file
            else:
                print "failed to copy %s" % file
            return succ
        else:
            raise ValueError("mode %s unrecognised" % self.mode)


if __name__ == '__main__':
    args = sys.argv[1:]
    g = Gridftp()
    g.parse_args(args)
    succ = True
    for file in g.files:
        succ1 = g.do_transfer(file)
        succ = succ and succ1

    if succ:
        sys.exit(0)
    else:
        sys.exit(1)
