# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import smtplib
import logging
import time

import Daemon
import LastMailedController

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class Informer(object):
    """
    Class to manage sending of mails.

    The ``held_errors`` attribute is a list of errors to send when a new
    message is allowed.
    """

    def __init__(self, mail_host, mail_sender, last_mailed_file,
                 interval_between_mails = 180):
        """
        Takes in ``config`` dictionary to set up stmp mail connection.
        """
        self.mail_host = mail_host
        self.mail_sender = mail_sender
        self.lmc = LastMailedController.LastMailedController(last_mailed_file, interval_between_mails)
        self.held_errors = []


    def notify(self, recipients, msg, subject):
        """
        Checks to see if we should send. Does so if ready. Otherwise just store messages to send later.
        """
        self.held_errors.append(msg)

        if self.lmc.shouldWeMail() == False:
            return False
        else:
            all_messages_in_one = "\r\n---\r\n".join(self.held_errors)
            self.sendEmailInBackground(recipients, all_messages_in_one, subject)
            self.held_errors = []
            return True


    def _sendMail(self, recipients, msg, subject):
        """
        Actually sends the message.
        Sends ``msg`` with ``subject`` to a list of ``recipients``.
        """
        log.warn("Sending mail with subject: %s" % subject)

        smtpServer = self.mail_host

        message = """From: %s
To: %s
Subject: %s

%s""" % (self.mail_sender, ";".join(recipients), subject, msg)

        print message, self.mail_sender, recipients
        s = smtplib.SMTP()
        s.connect(smtpServer)
        print "connected..."
        s.sendmail(self.mail_sender, recipients, message)
        print "Sent..."
        s.close()

        log.warn("Completed send of mail.")
        return True


    def _buildMessage(self, inventory):
        """
        Returns a string containing the file inventory formatted appropriately for
        an e-mail message.
        """
        pass


    def sendEmailInBackground(self, recipients, msg, subject):
        """
        as notify() but launch a subprocess (and do not wait)
        """
        #Daemon.DaemonCtl(self._sendMail, args=[recipients, msg, subject], doubleFork=True)
        apply(self._sendMail, [recipients, msg, subject])


if __name__ == "__main__":

    x = Informer("151.170.240.57", "ag.stephens@metoffice.gov.uk", "/tmp/test_last_mailed_file", 3)
    x.sendEmailInBackground(["stephens.ag@gmail.com"], "Some test number 2", "A test Informer alert")
    print "sent a message"

