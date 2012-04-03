# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os
import time
import hashlib

import sys
this_dir = os.path.dirname(__file__)
top_dir = os.path.abspath(os.path.dirname(this_dir + "../"))
lib_dir = os.path.join(top_dir, "lib")
sys.path.append(lib_dir)

from .FileUtils import futils

class TransferUtils:
    """
    Utilities class for TransferBase
    """
    #def __init__(self, datadir):
    #  self.datadir = datadir

    @staticmethod
    def timeStamp():
        """
        A timestamp that is designed to be part of a filename to ensure
        uniqueness.
        """
        return "%.2f" % time.time()

    @staticmethod
    def calcChecksum(file_path):
        """
        NOTE: THIS MIGHT NOT BE BEST METHOD FOR CALCULATING MD5 checksum!!!!
        comment from Alan - tested it and it agrees with md5sum command - 
        haven't tested performance          
        """
        block_size = 0x10000

        def upd(m, data):
            m.update(data)
            return m

        fd = open(file_path, "rb")
        try:
            contents = iter(lambda: fd.read(block_size), "")
            m = reduce(upd, contents, hashlib.md5())
            checksum = m.hexdigest()
        finally:
            fd.close()

        return checksum

    @staticmethod
    def getPathInDir(filename, dirname):
        """
        Return full path in specified directory
        """
        # filename should not contain "/" so we only take its basename
        return os.path.join(dirname, os.path.basename(filename))

    '''
    getPaths is called to get the list of files this Transfer class has and
    traverse any directories that may be present
    The method returns a list of all files that will be transfered
    '''
    @staticmethod
    def getPaths(srcpath, files):
        fl2 = []
        op = os.getcwd()
        np = os.chdir(srcpath)
        for f in files:
            if os.path.isdir(f) == True:
                fl2.append(f + "/")
                for dirname, dirnames, filenames in os.walk(f):
                    for subdirname in dirnames:
                        fl2.append(os.path.join(dirname, subdirname, "/"))
                    for filename in filenames:
                        fl2.append(os.path.join(dirname, filename))
            else:
                fl2.append(f)
        os.chdir(op)
        return fl2

    @staticmethod
    def getPlainFileName(datadir, item, dir_size_limit, zipdir = True):
        """
        item is an entry in the dataset directory, which may be file or directory
        if a plain file, return the name
        if a directory, zip it up and return the zip file name
        if anything that can't be transferred, return None
        """

        path = os.path.join(datadir, os.path.basename(item))
        if (not os.path.exists(path)):
            print path
            return None

        if os.path.islink(path):
            return None

        if os.path.isfile(path):
            return item
        elif os.path.isdir(path) and zipdir:
            size = futils.getDirSize(path)  # this is in bytes, limit is in MB
            if size < 0:
                return None
            if dir_size_limit and (size > dir_size_limit  * 1048576):
                return None

            resp = futils.zipDir(path)
            if not resp:
                return None
            zip_file = resp.data
            resp = futils.deleteDir(path)
            return zip_file
        elif os.path.isdir(path) and zipdir == False:
            return item
        else:
            return None

    @staticmethod
    def quarantine(file_name, data_dir, quarantine_dir):
        """
        Move specified file into the quarantine directory,
        If necessary timestamp the filename to prevent overwriting.
        """
        futils.ensureDirExists(quarantine_dir)
        file_path = TransferUtils.getPathInDir(file_name, data_dir)
        q_file_path = TransferUtils.getPathInDir(file_name, quarantine_dir)
        if os.path.exists(file_path):
            while os.path.exists(q_file_path):
                q_file_path += "." + TransferUtils.timeStamp()
                os.rename(file_path, q_file_path)


