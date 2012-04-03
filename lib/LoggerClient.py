# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os
import re
import logging, logging.handlers
import signal

import AlertEmailer


class LoggerClient(object):

    """
    Class that connects to a running LoggerServer, and also sends
    email for messages which exceed a certain level.

    (The sending email could perhaps be moved to the server - it is
    possible to test the level in the server - but this way the app
    can decide whether to send email by specifying send_email=True/False
    on logMessage(), overriding the config-based decision.)
    """

    def __init__(self, config,
                 host = 'localhost', 
                 port = None,
                 tag = "MiStaMover", name = None,
                 debug_on = False):
        """
        Arg config is the DatasetConfig or GlobalConfig object
        
        optional args:
          host, port are where to log to (defaults should normally work)
          tag is a string which the server will used to tag the message
          name is a longer description which may be used when sending email
          debug_on is a boolean for logging to terminal as well as log files.
        """

        lconfig = config["logging"]

        self.default_level = logging.INFO
        level_spec = lconfig["log_level"]
        level = self.lookupLevel(level_spec)

        if port == None:
            port = lconfig["port"]

        email_spec = config["email"]["threshold"]
        self.email_level = self.lookupLevel(email_spec)
        self.tag = tag
        self.debug_on = debug_on
   
        logger = logging.getLogger(tag)
        logger.setLevel(level)
   
        socketHandler = logging.handlers.SocketHandler(host, port)
        logger.addHandler(socketHandler)
        self.logger = logger
        self.mailer = AlertEmailer.AlertEmailer(config,
                                                name or tag)

        self.emails = []
        self.email_timer = 300
        if config.checkSet("logging.email_timer"):
            self.email_timer = config.get("logging.email_timer")
        signal.signal(signal.SIGALRM, self.sendEmails)
        signal.alarm(self.email_timer)

    def pushMessage(self, message):
        self.emails.append(message)

    def sendEmails(self, signum, frame):
        self.info("sendEmails")
        # make uniq
        eset = set(self.emails)
        for m in list(eset):
            self.mailer.sendEmailInBackground(m)
        self.emails = []
        signal.alarm(self.email_timer)

    def lookupLevel(self, level_spec):
        """
        Turn 'INFO' into logging.INFO etc
        """
        if type(level_spec) == type(self.default_level):
            return level_spec

        if not level_spec:
            return self.default_level

        try:
            return getattr(logging, level_spec)
        except AttributeError:
            return self.default_level


    def whetherToSendEmail(self, level, send_email):
        """
        send_email can be: None -- (decide based on message level and threshold),
                           True/False -- respond unconditionally
        """
        if send_email == None:
            return level >= self.email_level
        else:
            return send_email


    def logMessage(self, level_spec, message, send_email=None):
        """
        log a messages at a given level (level_spec can be e.g. either 
           logging.INFO or string e.g. "INFO").

        Also decides whether to send email, but can pass optional arg to 
        force this as yes/no.
        """
        level = self.lookupLevel(level_spec)
        if self.whetherToSendEmail(level, send_email):
            self.pushMessage(message)
            #self.mailer.sendEmailInBackground(message)
    
        self.prefix = "(pid=%s) " % os.getpid()
        self.logger.log(level, self.prefix + message)

        if self.debug_on:
            print "LOG MESSAGE: %s: %s" % (level, self.prefix + message)


    def debug(self, message, **kwargs):
        """
        Log a message at DEBUG level
        """
        return self.logMessage(logging.DEBUG, message, **kwargs)


    def info(self, message, **kwargs):
        """
        Log a message at INFO level
        """
        return self.logMessage(logging.INFO, message, **kwargs)


    def warn(self, message, **kwargs):
        """
        Log a message at WARN level
        """
        return self.logMessage(logging.WARN, message, **kwargs)


    def error(self, message, **kwargs):
        """
        Log a message at ERROR level
        """
        return self.logMessage(logging.ERROR, message, **kwargs)


    def critical(self, message, **kwargs):
        """
        Log a message at CRITICAL level
        """
        return self.logMessage(logging.CRITICAL, message, **kwargs)


    def exportMethods(self, obj):
        """
        Exports the main methods into another object, for 
        convenience.

        Calling code would do something like:
            self.logger = LoggerClient()
            self.logger.exportMethods(self)

        and can thereafter do
            self.info(....)

        instead of "self.logger.info" everywhere
        """
        for method in ['debug', 'info', 'warn', 'error', 'critical']:
            setattr(obj, method, getattr(self, method))

    

if __name__ == '__main__':

    from TestConfig import gc
  
    l = LoggerClient(gc, tag = "mytest", name = "my test code")
    l.debug("this is an debug message")
    l.info("this is an info message")
    l.warn("this is a warning")
    #l.error("this is an error")
