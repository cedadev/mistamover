.. _testing:

Testing Framework
=================

The MiStaMover tool has a testing framework which is designed to show that individual modules work as designed.

The test config files and programs can be found in a subdirectory in the MiStaMover source tree called *test*

The tests can be run by changing to the MiStaMover directory and typing

`python test/myproxytest.py --runPipe`

This will cause the *myproxytest.py* test to be run - as some tests can perform mulitple things the command line argument is used to determine which operation to run (in this case --runPipe)

The following tests are available

emailtest.py
  - uses email_global.ini
  - starts a log server, creates an info message and emails a critical message

ftptest.py
  - uses ftp_global.ini data_stream_ftp.ini
  - checks that config is valid, creates stopfile, creates push command, creates receipt command
  - creates thank you file

globustest.py
  - uses rsync_global.ini data_stream_rsync.ini
  - creates a transfer base, creates a command to test grid ftp credentials

rsynctest.py
  - uses rsync_global.ini data_stream_rsync.ini
  - checks config, sets stop file command, sets up push command

rsynctransfertest.py
  - uses rsync_global2.ini data_stream_rsync2.ini
  - sets up RsyncTransfer instance, transfers a file to another directory

stagercontrollertest.py
  - uses rsync_global_ini data_stream_rsync.ini
  - sets up a stagercontroller instance and dumps the config

transferbasetest.py
  - uses rsync_global.ini data_stream_rsync.ini
  - sets up a transferbase instance, runs a command ls -l via the transferdata method

transferbasetest2.py
  - sets up a transferbase - uses a mock object for logging
  - runs an rsync command over the transferdata method

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search
