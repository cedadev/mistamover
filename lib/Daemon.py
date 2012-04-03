# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Daemon.py - daemon module
========================= 

Module holds a couple of classes related to launching code in a daemon process.

The key usage concept is that the parent process should instantiate 
``DaemonCtl``, passing the method for the daemon to run, and the arguments
to pass to that method.  This will launch a daemon which runs as 
specified, and the DaemonCtl object that is instantated in the
parent process then has methods for communicating with the daemon and
testing return values.

The ``Daemon`` class is instantiated in the daemon. However, the user-provided
method should probably not refer to this directly, and indeed the method does
not need to be written with any awareness that it is running as a daemon.
However, a module-level function called weWereSignalled() is provided so that
the daemon can test whether signals were received.

"""

# Standard library imports
import os
import signal
import types
import time
import sys

# local imports
from ProcName import setProcName

# Classes
class DaemonBase(object):
    """
    .. class:: DaemonBase()

    Base class for deamon classes. Has one method to get a signal.
    """

    def getSignal(self, sig):
        """
        .. method:: sig

        Return a signal number from what may be a name or number.
        """
        if isinstance(sig, str):
            return getattr(signal, "SIG%s" % sig)
        return sig


class DaemonCtl(DaemonBase):
    """
    .. class:: DaemonCtl(DaemonBase)

    Daemon control code.  To instantiate in the parent process.
    """

    def __init__(self, method = None, doubleFork = False,
                 description = None,
                 *args, **kwargs):
        """
        .. method:: __init__(self)

          method: String - name of method
          doubleFork: Boolean - which avoids leaving zombie processes if True 
          description: String
          *args: ?
          *kwargs: ?

        """
        self.pid = None
        self.status = None
        self.description = description
        self.doubleFork = doubleFork
        if method:
            self.launch(method, *args, **kwargs)


    def launch(self, *args, **kwargs):
        """
        .. method:: launch(self, *args, **kwargs)

        Launch a daemon process.
        The arguments in ``args`` and ``kwargs`` are passed to the Daemon instance.

        Returns the process id.
        """
        pid = self.fork()
        if pid == 0:
            # child
            if isinstance(self.description, str):
                setProcName(self.description)
            Daemon(*args, **kwargs)
            # Should not reach the next line!
            assert(False)

        self.pid = pid
        return pid


    def fork(self):
        """
        .. method:: fork(self)

        Wrapper around `self.__fork()`

        Returns the forked process id.
        """
        pid = self._fork()
        if pid == 0:
            _thisDaemon.reset()
        return pid
        

    def _fork(self):
        """
        .. method:: _fork()

        Forks a process.

        If ``doubleFork`` was set when creating the instance, then use a double
        fork, which avoids zombies but loses much useful communication with the
        daemon - use it for stuff you want to launch and then forget about.

        Returns the forked process id.
        """
        if not self.doubleFork:
            return os.fork()            

        else:
            # double fork
            pid1 = os.fork()
            if pid1 == 0:
                # child
                pid2 = os.fork()
                if pid2 == 0:
                    # grandchild                    
                    return 0
                else:
                    # get the PID back via exit status
                    sys.exit(pid2)
            else:
                p, status = os.waitpid(pid1, 0)
                pid = status / 256
                return pid


    def sendSignal(self, sig = None):
        """
        .. method:: sendSignal(self, sig = None)

          sig: is the signal number or string.

        Sends a signal to the daemon process
        """
        try:
            os.kill(self.pid, self.getSignal(sig))
        except:
            pass


    def shutdown(self):
        """
        .. method:: shutdown(self)

        Sends term, then kill signal.  

        Returns exit value.
        """
        self.sendSignal("TERM")

        for loop in range(10):
            time.sleep(0.1)
            status = self.getStatus(wait=False)

            if status != None:
                return status

        self.sendSignal("KILL")
        return self.getStatus(wait=True)
        

    def isRunning(self):
        """
        .. method:: isRunning(self)

        Check if the daemon is running

        Returns a boolean of whether the process is running or not.
        """
        # see if the pid still exists
        try:
            os.kill(self.pid, 0)
        except:
            # the pid is not present
            self.pid = None
            return False

        if self.pid is None:
            return False

        return self.getStatus(wait=False) is None


    def getStatus(self, wait=False):
        """
        .. method:: getStatus(self, wait=False)

          wait: Boolean, if ``wait`` is set then wait until it finishes.

        Returns the return status of the daemon.
        """
        if self.pid is None:
            # not launched yet (or has been killed)
            return None

        if self.status is not None:
            # already tested for - return same again
            return self.status

        if wait:
            opts = 0
        else:
            opts = os.WNOHANG
        pid, status = os.waitpid(self.pid, opts)
        if pid == 0:
            # still running
            return None

        status /= 256  # convert to actual exit status
        self.status = status
        return status

#---------------------------------------------

class SimpleContainer(object):
    """
    Simple mutable object for storing a single item.
    """
    def reset(self):
        if self.isSet():
            del(self.x)
    def get(self):
        return self.x
    def set(self, x):
        self.x = x
    def isSet(self):
        return hasattr(self, 'x')

# a module-level mutable object where we can store any Daemon
# object relevant to the current process - gets cleared in DaemonCtl.fork()
# and set in Daemon.__init__
_thisDaemon = SimpleContainer()

    

def weWereSignalled(sig, requireDaemon = False):
    """
    Code that can be called by the daemon to test whether a given signal
    was received (which needs to have been a signal specified at the time
    when the daemon was launched - see argument "signals" in Daemon.__init__
    that are passed via DaemonCtl.launch). Note that "sig" may be a name
    (e.g. USR1) or a number.

    If the process wasn't actually launched as a daemon by this module, 
    then the action depends on whether optional argument requireDaemon is 
    set (raise an exception) or not (just return False).
    """
    try:
        obj = _thisDaemon.get()
    except:
        if not requireDaemon:
            return False
        raise Exception("daemon not initialised")
    return obj.wasSignalled(sig)    


class Daemon(DaemonBase):
    """
    .. class:: Daemon(DaemonBase)

    Daemon running code.  To instantiate in the child (daemon) process itself.

    Note this is done automagically - the user code does not have to care 
    about this.
    """

    def __init__(self,
                 method,
                 args = [],
                 kwargs = {},
                 logfile = None,
                 log_append = False,
                 signals=["USR1", "USR2"]):
        """
        .. method:: __init__(self...)

        Runs the ``method`` provided by the user.
        """
        if _thisDaemon.isSet():
            raise Exception("this process (%s) has already initialised the daemon" %
                            os.getpid())
        _thisDaemon.set(self)

        self._initSignals(signals)
        try:
            os.close(0)  # stdin
        except:
            pass

        logfh = None
        if logfile:
            try:
                flags = os.O_RDWR | os.O_CREAT
                if log_append:
                    flags |= os.O_APPEND
                logfh = os.open(logfile, flags)

                # Stdout to log file
                os.dup2(logfh, 1)
                #Stderr to log file
                os.dup2(logfh, 2)
            except OSError, err:
                print "Could not open log file '%s' for daemon: %s " % \
                      (logfile, err.strerror)

        if logfh:
            print "Daemon started at %s, calling %s" % (time.asctime(),
                                                        method.__name__)
        retval = method(*args, **kwargs)

        if logfh:
            print "Daemon ended at %s\n" % time.asctime()

        self._doExit(retval)


    def _doExit(self, retval):
        """
        .. method:: _doExit(self, retval)

          retval: Return value of method.

        Exits process with exit code based on method return value
        """
        exitval = 0
        if isinstance(retval, int):
            exitval = retval

        # Note: os._exit() loses buffered I/O
        sys.exit(exitval)


    def wasSignalled(self, sig):
        """
        .. method:: wasSignalled(self, sig)

          sig: signal value or string

        Tests if we have received a signal from the parent and returns a boolean.
        """
        signum = self.getSignal(sig)

        if signum not in self.signalsReceived:
            raise ValueError("handler not in use for signal %s" % signum)

        return self.signalsReceived[signum]

        
    def _receiveSignal(self, sig):
        self.signalsReceived[sig] = True


    def _initSignals(self, signals):
        """
        Set up handlers which record arrival of each of the named signals.

        Also ignore SIGINT (keyboard interrupt) if not explicitly specified.
        """
        self.signalsReceived = {}
        for sig in signals:
            signum = self.getSignal(sig)
            self.signalsReceived[signum] = False

        for signum in self.signalsReceived.keys():
            signal.signal(signum,
                          lambda signo, frame: self._receiveSignal(signo))

        for ignore_signal in (signal.SIGINT,):
            if ignore_signal not in self.signalsReceived:
                signal.signal(ignore_signal, signal.SIG_IGN)


#-----------------------------------------------------------------------

if __name__ == '__main__':

    # Test the DaemonCtl class
    from time import sleep

    def daemonCode(n):
        for i in range(n):
            sleep(1)
            print "Received USR1=%s USR2=%s" % \
                  (weWereSignalled("USR1"), 
                   weWereSignalled("USR2"))
        return 2

    class TestObject:
        def __init__(self, data):
            self.data = data
            
        def myMethod(self, str1, str2):
            print str1, str2, self.data
            while True:
                if weWereSignalled("USR1"):
                    return 1
                print "waiting...."
                sleep(1)            
    

    # a daemon that calls a function
    daemon1 = DaemonCtl(daemonCode,
                        logfile = 'daemon.log',
                        log_append = True,
                        args = [4])

    # a daemon that calls a class method
    t = TestObject("foo")
    daemon2 = DaemonCtl(t.myMethod,
                        logfile = 'daemon2.log',
                        args = ["hello", "world"])

    sleep(1.5)
    daemon1.sendSignal("USR1")
    sleep(1)
    daemon1.sendSignal("USR2")

    while daemon1.isRunning():
        print "daemon1 is running...."
        sleep(1)

    print "daemon1 exited with %s" % daemon1.getStatus()

    daemon2.sendSignal("USR1")
    print "daemon2 exited with %s" % daemon2.getStatus(wait = True)    

    daemon3 = DaemonCtl(time.sleep, args=[4], doubleFork=True)
    for i in range(6):
        os.system("ps ux | grep python")
        print "-----------"
        time.sleep(1)


