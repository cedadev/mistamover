# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os
import time

from AbstractDatasetController import AbstractDatasetController
import ReceiptFile
import ControlFile
import ThankyouFile
from StatusFlag import status
from FileUtils import futils

class DatasetArrivalMonitor(AbstractDatasetController):
    """
    Sub-process that monitors arrivals,
    runs checksums, generates receipt (checksum) files,
    delivers good files to data_stream dir (see next para),
    and tests for "thank you" files (acknowledgement of
    receipt files) in which case it deletes the receipt
    files and the "thank you" files themselves.

    This is set up to look in an "incoming" directory, and when a
    data file has a good checksum then deliver it to the data_stream
    directory for the DatasetTransferController.  This means that the 
    DatasetTransferController will just look for files appearing in 
    the data_stream directory and can assume their integrity - it knows
    nothing about the arrival monitor - only the top-level 
    MiStaMoverController knows that it launched an arrival monitor.

    Note also that it does not look at any data files until 
    these are referred to by a control file.  So partially arrived
    data files are not a problem.  BUT it is the sender's 
    responsibility to send the control file AFTER the data file.
    """
    short_name = "arrmon"
    long_name = "dataset arrival monitor"

    max_age_for_bad_ctl_file = 10  # FIXME(?): hard-coded constant


    def setVarsFromConfig(self):
        """
        see also method with this name in base class (which is called)
        """
        self.incoming_dir = self.dconfig.get("incoming.directory")
        self.ctl_suffix = "." + self.dconfig.get("incoming.control_file_extension")
        self.thankyou_suffix = "." + self.dconfig.get("incoming.thankyou_file_extension")
        AbstractDatasetController.setVarsFromConfig(self)

        
    def getPathInIncoming(self, filename):
        """
        given basename return full path name in incoming
        """
        return self.getPathInDir(filename, self.incoming_dir)


    def listIncomingDir(self, *args, **kwargs):
        """
        Returns list of files (basenames) in incoming dir.
        Defaults to excluding dotfiles, but called with include_dotfiles
        when we want to see the control files.
        """
        return self.listDir(self.incoming_dir, *args, **kwargs)


    def isControlFile(self, filename):
        """
        Test if file is a control file (returns boolean)
        """
        return filename.endswith(self.ctl_suffix)


    def createReceiptFile(self, rcpt_file_name, data_file_name, rcpt_data):
        """
        create a receipt file in the incoming directory
           rcpt_file_name is the basename for the file to create
           data_file_name is the basename for the data file
           rcpt_data is a list of [status, size, checksum] (or shorter list if any 
             of these are not supplied)
        """
        rcpt_file_path = self.getPathInIncoming(rcpt_file_name)        
        #
        # The thank-you file name contains a time stamp so that on retries of a
        # given data file, it will not overwrite one from a previous attempt.
        # Now in fact, the file name for the receipt file already contains 
        # the attempt number, so in principle we could extract that part and 
        # use it instead of the timestamp - but we don't want to assume anything
        # about the receipt filename.
        #
        thankyou_file_name = (".%s.%s%s" %
                              (data_file_name,
                               self.timeStamp(),
                               self.thankyou_suffix))
        rcpt_args = [data_file_name] + rcpt_data
        rcpt_file = ReceiptFile.ReceiptFile(rcpt_file_path,
                                            can_overwrite=True)
        kwargs = {"thankyou_file": thankyou_file_name}
        rcpt_file.create(*rcpt_args, **kwargs)
        self.debug("made receipt file %s, want thankyou file %s" %
                   (rcpt_file_name, thankyou_file_name))
        

    def respondToControlFile(self, filename):
        """
        Respond to a control file, generating receipt file with appropriate
        response, and delivering the data file to the data_stream directory if
        appropriate.

        Argument is the basename of the control file.

        Returns the data file name if it was all okay, otherwise None
        """
        data_file_delivered = False
        ctl_path = self.getPathInIncoming(filename)
        try:                        
            ctl_file = ControlFile.ControlFile(ctl_path)
            filename, correct_size, correct_cksum, rcpt_file_name \
                      = ctl_file.read()
        except ControlFile.Invalid:
            # an invalid control file - either it is
            # very recent or it is stale

            if futils.getFileAge(ctl_path) < self.max_age_for_bad_ctl_file:
                # invalid but recent control file
                # just ignore it, may still be coming in.                
                return
            else:
                # We can't really respond because the control file specifies the
                # name of the receipt file to use, and we couldn't parse the control
                # file.  Just log it.  The sender will time out and then retry.
                self.warn("Unparseable control file %s" % filename)
                futils.deleteFile(ctl_path)
                return
        else:
            # good control file
            self.info("control file %s says %s size %s cksum %s" %
                      (ctl_path, filename, correct_size, correct_cksum))
            file_path = self.getPathInIncoming(filename)
            rcpt_data = self.checkFile(file_path, correct_size,
                                       correct_cksum)        

        if rcpt_data[0] == ReceiptFile.SUCCESS:
            # we liked it - deliver the datafile to the data_stream dir
            try:
                os.rename(file_path,
                          self.getPathInDataDir(filename))
                data_file_delivered = True
                self.info("File %s accepted (size %d, cksum %s)" %
                          (filename, correct_size, correct_cksum))
            except OSError:
                self.error("I/O error testing file %s" % filename)

        else:
            # we didn't like the data file so delete it
            futils.deleteFile(file_path)
            self.warn("File %s rejected" % filename)

        # delete control file before making receipt file - reason is that if we are heavily loaded,
        # and the checksum is bad, it is just possible (though unlikely) that the remote end
        # might have already started sending the control file for the next attempt before we
        # get round to deleting what we think is the "old" one

        futils.deleteFile(ctl_path)
        self.createReceiptFile(rcpt_file_name, filename, rcpt_data)

        self.debug("deleted control file %s" % ctl_path)

        if data_file_delivered:
            return filename


    def isThankyouFile(self, filename):
        return filename.endswith(self.thankyou_suffix)


    def respondToThankyouFile(self, filename):
        """
        deal with a thank you file: delete the receipt file and the
        thank you file itself

        (input filename is the basename)
        """
        thankyou_path = self.getPathInIncoming(filename)
        try:
            thankyou_file = ThankyouFile.ThankyouFile(thankyou_path)
            (rcpt_file_name,) = thankyou_file.read()
        except ThankyouFile.Invalid:
            if futils.getFileAge(thankyou_path) < self.max_age_for_bad_ctl_file:
                return
            else:
                self.warn("Unparseable thank-you file %s" % thankyou_path)
        else:
            rcpt_file_path = self.getPathInIncoming(rcpt_file_name)
            futils.deleteFile(rcpt_file_path)
            self.debug("deleted receipt file %s" % rcpt_file_path)
            
        futils.deleteFile(thankyou_path)
        self.debug("deleted thankyou file %s" % thankyou_path)
            

    def checkFile(self, file_path, correct_size, correct_cksum):
        """
        Check a file and return data to write to the receipt file
        """
        if not os.path.exists(file_path):
            self.warn("%s: no such file" % file_path)
            return [ReceiptFile.NO_SUCH_FILE]
        try:
            actual_size = futils.getSize(file_path)
            if actual_size != correct_size:
                self.warn("%s actual size %s correct size %s" %
                                 (file_path, actual_size, correct_size))
                return [ReceiptFile.BAD_SIZE, actual_size]
            else:
                actual_cksum = futils.calcChecksum(file_path)
                if actual_cksum != correct_cksum:
                    self.warn("%s actual cksum %s correct cksum %s" %
                                     (file_path, actual_cksum, correct_cksum))
                    return [ReceiptFile.BAD_CKSUM, actual_size, actual_cksum]
                else:
                    return [ReceiptFile.SUCCESS, actual_size, actual_cksum]
        except IOError:
            return [ReceiptFile.IO_ERROR]


    def monitor(self):
        """
        Ongoing monitoring of process unless told to stop.
        """
        
        futils.ensureDirExists(self.dataset_dir)
        futils.ensureDirExists(self.incoming_dir)

        while True:

            self.updateStatusAndConfig()
            if self.status == status.STOPPED:
                return self.status
            
            items = self.listIncomingDir(include_dotfiles = True)

            for item in items:
                if self.isControlFile(item):
                    self.respondToControlFile(item)
                elif self.isThankyouFile(item):
                    self.respondToThankyouFile(item)

            time.sleep(self.poll_interval)
        


if __name__ == '__main__':
    import DatasetConfig
    os.environ["CONFIG__global__top"] = ".."
    dc = DatasetConfig.DatasetConfig("mytest", "../conf/global.ini")
    dc['logging']['log_level'] = 'DEBUG'
    
    d = DatasetArrivalMonitor(dc)
    d.monitor()
