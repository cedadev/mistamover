# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os
import stat
import time
import hashlib 

import Response
import MyZipFile


class _SizeAdder(object):
    """
    Helper for FileUtils.getDirSize()
    Provides add() that we can call from FileUtils.recurseDir()
    """
    def __init__(self, futils):
        self.total = 0
        self.futils = futils
    def add(self, file):
        try:
            self.total += self.futils.getSize(file)
            return Response.success()
        except OSError:
            return Response.failure()



class FileUtils(object):
    """
    Class acting as a container for a selection of useful file utilities.
    """
    def calcChecksum(self, file_path):
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


    def getDiskSpace(self, path, getNonRoot=False):
        """
        Get total and free disk space for a given path as a two-element
        tuple (total, free) in KB.

        If optional argument getNonRoot is set, and a proportion of the disk
        is reserved for root, then return only the free space available for
        non-root users.
        """
        try:
            statData = os.statvfs(path)
        except OSError:
            return None

        (blockSize, fragmentSize,
         totalBlocks, freeBlocks, availBlocks,
         totalFiles, freeFiles, availFiles,
         mountFlags, maxFilenameLen) = statData

        units = 1024
        total = totalBlocks * blockSize / units
        if getNonRoot:
            free = availBlocks * blockSize / units
        else:
            free = freeBlocks * blockSize / units

        return (total, free)


    def getSize(self, file_path):
        """
        get file size in bytes
        """
        return os.path.getsize(file_path)

   
    def getDirSize(self, dir_path):
        """
        recursively add sizes of regular files contained under directory 
        (in bytes)
        """
        adder = _SizeAdder(self)
        resp = self.recurseDir(dir_path,
                               adder.add,
                               None,
                               regular_files_only = True)
        if not resp:
            return -1
        else:
            return adder.total


    def getLastUpdatedTime(self, file_path):
        """
        get file mtime
        """
        return os.path.getmtime(file_path)

    
    def getCtimeOrNone(self, file_path):
        """
        Get ctime, or if an error then return None
        """
        try:
            return os.path.getctime(file_path)
        except OSError:            
            return None
    

    def ensureReadWrite(self, path):
        """
        ensure we have both read and write access to a given path
        (which should already exist) 
        """
        if not (os.access(path, os.W_OK) and os.access(path, os.R_OK)):
            # not writable - can we make it so?
            stat_data = os.stat(path)
            owner = stat_data.st_uid
            me = os.geteuid()
            if owner == me:
                mode = stat_data.st_mode
                mode |= stat.S_IRUSR
                mode |= stat.S_IWUSR
                # if it's a directory, add execute as well
                if stat.S_ISDIR(mode):
                    mode |= stat.S_IXUSR
                os.chmod(path, mode & 07777)
            else:
                raise Exception("%s cannot be made writable" % path)
                

    def ensureDirExists(self, dir_path, ensure_read_write = True):
        """
        Make sure a directory exists.  By default it also checks that it is
        writable.  Creates parent directories as necessary.
        """
        if not os.path.exists(dir_path):
            parent = os.path.dirname(dir_path)
            self.ensureDirExists(parent, ensure_read_write = True)
            try:
                os.mkdir(dir_path)
            except OSError:
                # if there is a race condition between two processes, we may
                # get an exception for the actually harmless condition that we
                # cannot create directory because the other one already did -
                # so only raise the exception if no directory was created
                if os.path.islink(dir_path) or not os.path.isdir(dir_path):
                    raise
            retval = 1
        else:
            if not os.path.isdir(dir_path):
                raise Exception("%s exists but is not a directory" % dir_path)
            retval = 0

        if ensure_read_write:
            self.ensureReadWrite(dir_path)

        return retval


    def _zipDir(self, dir_path, zip_file_path = None):
        """
        Zips a directory; the zip file will contain the regular files
        found under that directory.  Only the basename part of dir_path
        plus any subdirectories encountered will be stored in the directory
        names in the zip file.  Returns zip file path, which unless
        specified in optional input will default to dir_path + ".zip"
        """
        while dir_path[-1] == '/':
            dir_path = dir_path[: -1]
        
        if not zip_file_path:
            zip_file_path = dir_path + ".zip"

        z = MyZipFile.MyZipFile(zip_file_path, mode="w",
                                compression = MyZipFile.ZIP_DEFLATED,
                                remove_prefix = os.path.dirname(dir_path) + '/')

        resp = self.recurseDir(dir_path,
                               Response.Wrapper(z.writeWithoutPrefix),
                               None,
                               regular_files_only = True)
        resp.assert_()
        z.close()
        return zip_file_path


    def zipDir(self, *args, **kwargs):
        """
        As _zipDir, but returns a Response object
        """
        return Response.wrap(self._zipDir, *args, **kwargs)    


    # Functions deleteFile and deleteEmptyDir are like os.remove and
    # os.rmdir respectively, but they go via Response.Wrapper, so returns
    # a Response object, and any exceptions are just reflected in the
    # response contents

    # note - Response.Wrapper is callable but as it is not of type function 
    # it will not trigger python to turn it into a bound method; this is
    # good because we don't want the "self" argument
    deleteFile = Response.Wrapper(os.remove) 

    deleteEmptyDir = Response.Wrapper(os.rmdir)


    def recurseDir(self,
                   dir_path,
                   file_action,
                   dir_action,
                   regular_files_only = False,
                   stop_on_first_error = True):

        """
        recurse a directory doing actions
        file_action on each file, and dir_action on each directory
        these actions must return a Response object

        dir_path is a string (starting path)

        file_action is a callable which takes a path argument
           (called for either all non-directory items or just 
           reguar files, depending on optional arg regular_files_only)
            - or None if none required

        dir_action is a callable which takes a path argument
           (called for directories) - or None if none required - 
           NB this is just what to do with the directory entries 
           themselves - the recursion is already provided
           
        optional arg stop_on_first_error should be self-explanatory
        """
        
        resp = Response.success()
    
        try:
            entries = os.listdir(dir_path)  # FIXME(?) could use self.listDir() and add
                                            # "ignore dot files" functionality?
        except Exception, err:
            return Response.failure("%s: %s" % (Exception, err))
 
        for f in entries:
            whole_path = os.path.join(dir_path, f)
    
            if (not os.path.islink(whole_path)
                    and os.path.isdir(whole_path)):

                resp += self.recurseDir(whole_path,
                                        file_action,
                                        dir_action,
                                        regular_files_only = regular_files_only,
                                        stop_on_first_error = stop_on_first_error)
            else:
                if file_action:
                    if (not regular_files_only) or os.path.isfile(whole_path):
                        resp += file_action(whole_path)

            if stop_on_first_error and not resp:
                return resp

        if dir_action:
            resp += dir_action(dir_path)

        return resp
        

    def deleteDir(self, dir_path, **kwargs):
        """
        Delete a directory recursively (akin to rm -fr)

        Optional args (in particular stop_on_first_error) can be
        passed to recurseDir()
        """
        return (self.recurseDir(dir_path,
                                self.deleteFile,
                                self.deleteEmptyDir,
                                **kwargs)
                and Response.success("%s deleted" % dir_path))


    def getFileAge(self, file_path):
        """
        Get difference in seconds between current time and file mtime
        """
        return time.time() - self.getLastUpdatedTime(file_path)
        
    
    def isFileNewerThan(self, file_path, unix_time):
        """
        Returns True if file has been updated since unix_time or False.
        """
        last_updated = self.getLastUpdatedTime(file_path)
        # mtime is integer rounded down, round it up instead
        if last_updated + 1 > unix_time:
            return True
        else:
            return False


    def notDotFile(self, fname):
        return not fname.startswith(".")


    def listDir(self, dir_path, include_dotfiles = False, fullPaths = False,
                emptyListOnException = False, listOldestFirst = True):
        """
        List a directory.

        Default is to exclude dotfiles, and to return only relative pathnames.
        Override with optional args as required.

        if emptyListOnException set, returns [] if can't list the directory
        """
        try:
            if listOldestFirst == True:
                items_list = os.listdir(dir_path)

                if include_dotfiles == False:
                    items_list = [i for i in items_list if i[0] != "."]

                # Need to step through these
                mtime_items = [(os.stat(os.path.join(dir_path, item)).st_mtime, item) for item in items_list] 
                mtime_items.sort()
                items = [i[1] for i in mtime_items]
            else:
                items = os.listdir(dir_path)
        except OSError:
            if emptyListOnException:
                return []
            else:
                raise

        if not include_dotfiles:
            items = filter(self.notDotFile, items)

        if fullPaths:
            items = map(lambda filename: os.path.join(dir_path, filename),
                        items)

        return items


    def getMountPointForPath(self, dirpath):
        """
        Get the mount point (string) on which a path resides, or if it does not
        exist then the path name of the lowest-level parent directory which
        does exist (i.e. the filesystem on which it will end up on once
        directories are created)
        """
        if "/" not in dirpath:
            raise ValueError("%s must be full path" % dirpath)

        # remove any non-existing path elements
        while not os.path.exists(dirpath):
            assert (dirpath != '/')
            dirpath = os.path.dirname(dirpath)

        # resolve any symlinks
        dirpath = os.path.realpath(dirpath)

        # remove path elements to get the mount point
        while not os.path.ismount(dirpath):
            assert (dirpath != '/')
            dirpath = os.path.dirname(dirpath)

        return dirpath
            


futils = FileUtils()

