# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
A listening logging server for MiStaMover.  This logs to a file (only).

The main object instantiated in the calling code is LoggerServer,
which listens for messages on a port and logs them.  The classes
SingleFileLogger and MultiFileLogger are helpers that actually
log these to the relevant files.
"""

import os
#import time
import logging

import LogReceiver

class SingleFileLogger(object):
    """
    A logger class which logs all messages it receives to one file
    """

    def __init__(self, config, tag, formatter = None):
        """
        Inputs:  config should be a GlobalConfig / DatasetConfig object
        tag is a short tag name which will be used in the log filename
        """
        self.base_dir = config["logging"]["base_log_dir"]

        if formatter == None:
            formatter = logging.Formatter(fmt="[%(asctime)s] %(name)s(%(levelname)s) %(message)s",
                                           datefmt="%Y-%m-%d %H:%M:%S")
        self.formatter = formatter
        self.logger = self.makeLogger(tag)

    
    def makeLogger(self, tag):
        """
        Takes a tag (part of filename), and returns a logger object 
        from the logging module
        """
        pathname = self.getPath(tag)
        fh = logging.FileHandler(pathname)
        fh.setFormatter(self.formatter)
        #
        # If MiStaMover has already initialised the client before forking the
        # daemon, it will have done a getLogger() call already and added
        # the SocketHandler (client code) as a handler.  getLogger() will
        # return a cached copy if called again with the same logger name, and
        # we do NOT want to reuse this logger as the server logger, as it will
        # end up with a spurious additional client handler as well as the
        # server handler that we actually want, causing nasty infinite loops.
        # So force a different name by prepending "__SERVER__".
        #
        logger = logging.getLogger("__SERVER__" + tag)
        logger.addHandler(fh)
        return logger


    def getPath(self, tag):
        """
        Get full path for log file with given tag
        """
        filename = tag + ".log"
        return os.path.join(self.base_dir, filename)                


    def handle(self, record):
        """
        Handle a record (delegates it to the underlying logger object)
        """
        return self.logger.handle(record)


class MultiFileLogger(object):
    """
    A class whose 'handle' method will return the handle method of
    a different file logger class for each tag, so that different
    tags get logged to different files.

    The SingleFileLogger objects are created on the fly in handle()
    when new tags appear that are have not been seen yet, so there is
    no need to specify the set of possible files on instantiation

    e.g. if a message appears with tag "foo" it will start logging to 
    foo.log
    """

    def __init__(self, config):
        """
        Arg is  GlobalConfig / DatasetConfig object
        """
        self.config = config

        # a common formatter for all files - no need for the name in this case
        self.formatter = logging.Formatter(fmt="[%(asctime)s] %(levelname)s %(message)s",
                                           datefmt="%Y-%m-%d %H:%M:%S")
        self.loggers = {}


    def handle(self, record):
        """
        Handles a record by calling the necessary SingleFileLogger,
        creating it if not already cached.
        """
        tag = record.name
        if tag not in self.loggers:
            self.loggers[tag] = SingleFileLogger(self.config, tag,
                                                 formatter = self.formatter)
        return self.loggers[tag].handle(record)



class LoggerServer(object):
    """
    A top level logger server, which will receive messages on a port
    and pass them to either SingleFileLogger or MultiFileLogger
    """
    def __init__(self, config, multi=True):
        """
        instantiate with GlobalConfig / DatasetConfig object

        set "multi" to True/False depending whether single file or
        multi file logging is wanted
        """
        self.port = config['logging']['port'] \
                    or logging.handlers.DEFAULT_TCP_LOGGING_PORT
        self.host = 'localhost'
        self.config = config
        self.multi = multi

    def serve(self):
        """
        Main loop.
        """
        if self.multi:
            logger = MultiFileLogger(self.config)
        else:
            logger = SingleFileLogger(self.config, "MiStaMover")
            
        tcpserver = LogReceiver.LogRecordSocketReceiver(
                        logger, self.host, self.port)
        tcpserver.serve_until_stopped()


if __name__ == '__main__':

    import sys
    from TestConfig import gc

    server = LoggerServer(gc, multi=False)

    os.system("touch ../log/MiStaMover.log")
    pid = os.fork()
    if pid == 0:
        os.execvp("tail", ["tail", "-f", "../log/stager.log"])
        sys.exit()

    try:
        server.serve()

    except KeyboardInterrupt:
        os.kill(pid, 9)
