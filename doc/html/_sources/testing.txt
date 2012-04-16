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

.. _config_test_data:

Configuring a test data stream
------------------------------

MiStaMover can manage a number (up to 10 have been tested) of parallel data stream transfers. It requires a configuration file for each data stream and will monitor incoming directories and transfer files to outgoing directories for each stream. 

## AG :: the following is probably no longer relevant

In order to run a test, we need to create a test data stream. Since we imagine that most users will get started this way, we have provided a test data stream configuration file in the configuration directory called ``data stream_test1.ini``. In order for MiStaMover to know about this data stream its global configuration file (``global.ini``) needs to be informed about it. The default ``global.ini`` file includes the line::

  data_stream_list = test1

Now, we need some files to send. You can create a set of test files by running::

  export MY_STAGER=/usr/local/mistamover
  export LOG_DIR=$MY_STAGER/log
  export REMOTE_USERNAME=someone
  export REMOTE_HOST=some.server.some.where
  export SSH_KEY_FILE=$HOME/.ssh/identity
  export STAGER_CONF=$MY_STAGER/conf
  export STAGER_TEST=$MY_STAGER/data
  mistamover.py --create-test-data

Note that you do not have to set all of the above. The following variables have default values set to::

  REMOTE_USERNAME: $USER (environment variable)
  REMOTE_HOST:     localhost

This magically generates a set of files in the directory::

  /usr/local/mistamover/data/test1

The test data stream is configured to send all data to the ``REMOTE_HOST`` using the ``rsync_ssh`` transfer method (over ``ssh``). If this is not configured on your system then the test data stream will not work without further in the configuration file. 

However, in many cases you should now be able to run with:

  # The first line is required to tell MiStaMover where to find its default global configuration file
  bin/mistamover.py --debug

By choosing to run with the ``--debug`` argument switched on you can view the output from mistamover at the terminal. Alternatively, you can look at the log files _log_files.

The output should look something like::

  LOG MESSAGE: 10: (pid=17103) DSML init
  LOG MESSAGE: 20: (pid=17103) starting disk space monitor for filesystem /misc/humid1
  LOG MESSAGE: 20: (pid=17103) started log server
  LOG MESSAGE: 20: (pid=17103) starting procs for data stream test1
  LOG MESSAGE: 20: (pid=17103) starting Transfer Controller for data stream test1
  LOG MESSAGE: 20: (pid=17103) starting transfer controller for data stream test1
  LOG MESSAGE: 20: (pid=17109) startup
  LOG MESSAGE: 20: (pid=17109) Listing contents of data stream dir: /home/users/astephen/destroy/data/test1
  LOG MESSAGE: 20: (pid=17109) Processing Transfers...
  LOG MESSAGE: 20: (pid=17109) startup
  LOG MESSAGE: 20: (pid=17109) Listing contents of data stream dir: /home/users/astephen/destroy/data/test1
  LOG MESSAGE: 20: (pid=17109) Found a list of items to transfer of length '10', starting with: ['test1-0.nc', 'test1-1.nc', 'test1-2.nc']
  LOG MESSAGE: 20: (pid=17109) Starting transfer to: astephen@localhost:/home/users/astephen/destroy/received
  LOG MESSAGE: 10: (pid=17109) we will transfer test1-0.nc
  LOG MESSAGE: 10: (pid=17109) Not using arrival monitor
  LOG MESSAGE: 20: (pid=17109) Starting transfer to: astephen@localhost:/home/users/astephen/destroy/received
  LOG MESSAGE: 20: (pid=17109) Transfer succeeded: test1-0.nc

Trouble-shooting the test data stream configuration
---------------------------------------------------

If the test data stream did not run you may need to modify your configuration file(s). Please see the :ref:`configuration` section for more details.

Or it may be that you cannot run rsync over SSH. If that is the case you may wish to set the software up to run with FTP by customising the :ref:`configuration files <configuration>`.

#' Ag :: the above is probably not relevant

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search
