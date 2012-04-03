# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
TestDataset.py
==============

Holds the ``TestDataset`` class used to create a simple test dataset
to get users started.

"""

# Standard libary imports
import os
import sys
import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

env_vars_needed = ("STAGER_CONF", "REMOTE_USERNAME", "SSH_KEY_FILE", "STAGER_TEST", "LOG_DIR")


class TestDataset(object):

    def __init__(self, **kwargs):
 
        # Check we've got all required args:
        for arg in env_vars_needed:
            if not kwargs.has_key(arg):
                raise Exception("Keyword argument required but not provdided to TestDataset class instantiation: %s" % arg)

        for arg, value in kwargs.items():
            setattr(self, arg, value)
 
        self.basedir = self.STAGER_TEST
        if not os.path.isdir(self.basedir):
            log.info("Making base directory for test: %s" % self.basedir)
            os.mkdir(self.basedir)

        self.data_dir = os.path.join(self.basedir, "data")
        self.receiving_dir = os.path.join(self.basedir, "received")

        for sub_dir in (self.data_dir, self.receiving_dir):
            if not os.path.isdir(sub_dir):
                os.mkdir(sub_dir)

        self.config_dir = self.STAGER_CONF
        self._updateConfigFiles()

    def _updateConfigFiles(self):
        self._updateConfigFile("test1.tmpl", "dataset_test1.ini")
        self._updateConfigFile("global.tmpl", "global.ini")


    def _updateConfigFile(self, template, output):
        tmpl_file = os.path.join(self.config_dir, template)
        content = open(tmpl_file).read()
       
        for arg in env_vars_needed: 
            content = content.replace("::%s::" % arg, getattr(self, arg))

        config_file = os.path.join(self.config_dir, output)
        fout = open(config_file, "w")
        fout.write(content)
        fout.close()  
        log.info("Modified the '%s' configuration file ready for the test." % config_file) 
        

    def makeFile(self, name, size):
        s = "A" * size
        fout = open(name, "w")
        fout.write(s)
        fout.close()

        log.info("File created: %s with size: %d" % (name, os.path.getsize(name)))


    def makeDataset(self, name, n_files, size_scaler=1):
        ds_dir = os.path.join(self.data_dir, name) 
        if not os.path.isdir(ds_dir): os.mkdir(ds_dir)

        for i in range(n_files):
            fn = os.path.join(ds_dir, "%s-%d.nc" % (name, i))
            size = i * 10000 * size_scaler
            self.makeFile(fn, size)

    def create(self):
        self.makeDataset("test1", 10, size_scaler=100)
        #self.makeDataset("agtest2", 40)

def createTestDataset():
    """
    .. function: createTestDataset()

      Wrapper around TestDataset class.
    """
    env_var_map = {"STAGER_CONF": "as the Stager configuration directory (typically something like: `/usr/local/stager/conf`.",
        "REMOTE_USERNAME": "as the username that will log into the remote server.",
        "SSH_KEY_FILE": "as the SSH handshake identity file. E.g. `/home/me/.ssh/identity`.",
        "STAGER_TEST": "as the base directory for the test data and re-run the script. E.g. `export STAGER_TEST=/home/me/stager_test`.", 
        "LOG_DIR": "as the directory to write logs to. E.g. `/home/me/stager_logs`.",
        }

    kwargs = {}
    for key in env_vars_needed:
        item = os.environ.get(key, None)
        
        if not item:
            print "Please set %s environment variable %s" % (key, env_var_map[key])
            sys.exit()

        kwargs[key] = item

    x = apply(TestDataset, [], kwargs)
    x.create()

    log.info("""Test dataset created. You can now run the test with:
        %% export STAGER_DIR=%s
        %% stager.py --debug""" % kwargs["STAGER_CONF"])


if __name__ == "__main__":
 
    createTestDataset()
