# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
This is adapted from the example from the python docs.

http://docs.python.org/library/logging.html
"""

import cPickle
import logging
import logging.handlers
import SocketServer
import struct


class LogRecordStreamHandler(SocketServer.StreamRequestHandler):
    """Handler for a streaming logging request.

    This passes the request to the specified logger.
    The __init__ has an extra arg compared to the example in the python docs,
    which is the logger to use.
    """

    def __init__(self, logger, *args, **kwargs):
        self.mylogger = logger
        SocketServer.StreamRequestHandler.__init__(self, *args, **kwargs)

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while 1:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack(">L", chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self.unPickle(chunk)
            record = logging.makeLogRecord(obj)
            self.mylogger.handle(record)

    def unPickle(self, data):
        return cPickle.loads(data)


class LogRecordStreamHandlerGenerator(object):
    """
    The LogRecordStreamHandler above has an extra arg compared to what
    is in the python docs.  This generator class stores that extra arg
    and is then callable using the expected interface.
    """
    def __init__(self, logger):
        self.logger = logger
    def __call__(self, *args, **kwargs):
        return LogRecordStreamHandler(self.logger, *args, **kwargs)

class LogRecordSocketReceiver(SocketServer.ThreadingTCPServer):
    """simple TCP socket-based logging receiver suitable for testing.
    """

    allow_reuse_address = 1

    def __init__(self, logger,
                 host='localhost',
                 port=logging.handlers.DEFAULT_TCP_LOGGING_PORT):

        handler = LogRecordStreamHandlerGenerator(logger)

        SocketServer.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1
        self.logname = None

    def serve_until_stopped(self):
        import select
        abort = 0
        while not abort:
            try:
              rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
              if rd:
                  self.handle_request()
              abort = self.abort
            except:
              pass


        
    
if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger("test")
    r = LogRecordSocketReceiver(logger)
    r.serve_until_stopped()
