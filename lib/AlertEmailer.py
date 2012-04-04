# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import time 
import re
import smtplib
import commands
#from email.MIMEText import MIMEText

import Daemon
#import tempfile
import os

class AlertEmailer(object):
    """
    An emailer that provides the sendEmail() method to send email,
    whose only argument is the message and everything else is 
    taken from the config file
    """

    def __init__(self, config, name =" MiStaMover"):
        """
        "config" is the config object (global or dataset)

        "name" (optional) is a string that describes the subsystem, 
                 that will appear in the emails
        """
        self.last_sent_file = "/badcstager/badc1/last_sent_file.txt"
        econfig = config["email"]
        self.email_from = econfig["from"]
        self.email_recipients = self.getEmailRecipients(econfig["recipient"])
        self.email_subject = econfig["subject"] or "error from logger"
        self.email_smarthost = econfig["smarthost"] or "localhost"
        self.name = name
        self.hostname = self.getHostName()

    def getEmailRecipients(self, rcpt_spec):
        """
        Turn a line from the config file into a comma-separated string
        of receipients (suitable for smtplib)
        """
        if rcpt_spec == None:
            return None

        # may be space or comma separated - return comma separated
        rcpts = re.sub(",?\s+", ",", rcpt_spec).split(",")
        return rcpts #re.sub(",?\s+", ",", rcpt_spec)


    def getHostName(self, short=False):
        if short:
            command = "hostname -s"
        else:
            command = "hostname"
            return commands.getoutput(command)


    def sendEmail(self, message):
        """
        Send email message - only the body is passed in argument 'message',
        everything else is from the config file
        """
        if self._allowSend() == False:
            return True

        if not (self.email_from and self.email_recipients):
            return False

        smtpServer = self.email_smarthost

#        msg = MIMEText("Stager running on %s (sub-system '%s')\n reported the following:\n\n%s" %
#                       (self.hostname, self.name, message))
#        msg["From"] = self.email_from
#        msg["Subject"] = ("%s (%s)" %  (self.email_subject, self.name))
#        msg["To"] = self.email_recipients

        msg = "MiStaMover running on %s (sub-system '%s')\n reported the following:\n\n%s" % (self.hostname, self.name, message)

#        s.sendmail(self.email_from, self.email_recipients, msg.as_string())

        # mail to each separately
        for recipient in self.email_recipients:
            #print recipient
            s = smtplib.SMTP()
            s.connect(smtpServer)            
#print "\nMailing: %s\n\n" % recipient
            content = """To: %s
From: %s
Subject: %s
%s""" % (recipient, self.email_from, self.email_subject, msg)
#            print content
            s.sendmail(self.email_from, [recipient], content)
            s.close()

        return True


    def sendEmailInBackground(self, message):
        """
        as sendEmail() but launch a subprocess (and do not wait)
        """
        if self._allowSend() == False:
            return True

        Daemon.DaemonCtl(self.sendEmail, args=[message], doubleFork=True)


    def _getLastSent(self):
        if not os.path.exists(self.last_sent_file):
            return float(0)
        else:
            try:
                fhandle = open(self.last_sent_file)
            except:
                time.sleep(2)
                fhandle = open(self.last_sent_file)

        ls = float(fhandle.read())
        fhandle.close()
        return ls

    def _setLastSent(self):
        if os.path.exists(self.last_sent_file):
            ls = open(self.last_sent_file, "w")
            ls.write("%s" % time.time())
            ls.close() 

    def _allowSend(self):
        now = time.time()
        last_sent = self._getLastSent()

        if (now - last_sent) > (3600 * 12):
            self._setLastSent()
            return True
        else:
            return False


if __name__ == '__main__':

    from TestConfig import gc

    e = AlertEmailer(gc, name = "Traffic Conversion success")
    print "Allow send?", str(e._allowSend())
    e.sendEmail("this is a DIFFERENT test")

    
