.. _getting_started:

Getting Started
===============

MiStaMover has been built with the intention that it is simple to download, install, configure and run. It is packaged as a gzipped tar file so you can download it and install in a matter of minutes. This page explains how to create a test dataset and run mistamover to test it.

Downloading and Installing MiStaMover
-------------------------------------

Make sure you have at least Python 2.5 on your system. Then download the :ref:`current version of MiStaMover <current_source>`.

Unpack the source code with the ``tar`` command::

  tar -C <DIRECTORY> -xvzf mistamover-<VERSION>.tar.gz

Where ``<DIRECTORY>`` is the directory into which you want to unpack the source and ``<VERSION>`` is the version you have downloaded. This directory must exist before you unpack the code.

For example, you might do::

  mkdir $HOME/mstmvr
  VERSION=0.1.0-alpha
  tar -C $HOME/mstmvr -xvzf mistamover-${VERSION}.tar.gz
  
The Directory Structure
-----------------------

MiStaMover has a simple directory structure. Just change directory to where the code has been unpacked and you are ready to go::

  cd $HOME/mstmvr/mistamover-${VERSION}
  
The sub-directories are\:

``bin/``
  Contains the ``mistamover.py`` script used to run the tool, and other utility scripts.
    
``conf/``
  Contains the default ``global.ini`` configuration file and is the default location for 
    a data stream configuration files.
    
``doc/``
  Contains the documentation in the ``html/`` sub-directory.
    
``lib/``
  Contains the main library of python modules.
    
``log/``
  An empty directory that is the default location for MiStaMover log files.
    
``test/``
  Contains test code used when developing and extending MiStaMover.

Since the code is written in python there is nothing to build!

Note that it is possible to split the various directories across your linux distribution, for example moving the ``log/`` directory to a common logging location and the ``lib/`` directory into your python source. Be sure to make the appropriate changes to your configuration information and PYTHONPATH environment variable if you decide to move the directories.

Running MiStaMover
------------------

The best way to get started is to run MiStaMover as a :ref:`one-off process <One-off>`. This will work as follows:

 #. MiStaMover is run at the command line
 #. A global configuration file is specified
 #. The global configuration identifies one data stream to be transferred
 #. The data stream configuration file is read, specifying the incoming directory, transfer protocol, transfer mode (move or mirror) and target host details
 #. MiStaMover sets up a sub-process to manage that data stream
 #. The incoming directory is scanned for files and/or directories
 #. Each file and/or directory is copied to the target host
 #. The local version in the incoming directory is either deleted (for move) or untouched (for mirror)

The following options are available when running MiStaMover at the command line::

  bin/mistamover.py [ --one-off | --daemon | ] [<GLOBAL_CONFIG_FILE>]
  
Where only one of the first four arguments must be specified. The ``<GLOBAL_CONFIG_FILE>`` is the location of the global configuration file you wish to use. This is an optional argument for which the default location is ``conf/global.ini``.

**WARNING: The default transfer mode is "move". Do not set your incoming directory to a location in which you intend to keep data without setting the transfer mode to "mirror"!** 

We can run MiStaMover with::

  bin/mistamover.py --one-off conf/global.ini

However, it will just sit there and do nothing because we haven't configured it to work with any datasets.

Press ``Ctrl^C`` to quit MiStaMover and let's take a look at a global configuration file.

The Global Configuration File
-----------------------------

Note that all the sections and settings of the configuration files are described in the :ref:`Configuration Files <configuration>`_ section.

MiStaMover works by reading a single global configuration file (typically located at ``conf/global.ini``) which in turn defines a set of data streams in its ``global:data_streams`` setting. For each data stream found, a separate configuration file will be read and then a sub-process started to manage the transfers related to that specific data stream.

The following is a global configuration file that defines a data stream called *my_outputs*. It will transfer the data in "move" transfer mode (deleting the local version once successfully copied remotely)::

  # 
  # Global config file - can override values per dataset by giving them the 
  # same section and key in the dataset config file  
  #  
    
  [global] 
  
  # global section is intended for stuff which is unlikely to be overridden 
  # per-dataset (although technically there is nothing to prevent a 'global'
  # section in the dataset config file) 
   
  homedir = /home/users/me 
  top = /home/users/me/work 
  base_data_dir = $(global:top)/data
  config_dir = $(global:homedir)/mistamover/conf  
  base_incoming_dir = $(global:base_data_dir)/incoming  
  data_stream_list = my_outputs
  general_poll_interval = 3 
   
  [incoming]
  require_arrival_monitor = False
  control_file_extension = mistamover-ctrl-bes
  thankyou_file_extension = mistamover-thanks-bes
  stop_file = .stop 
   
  [outgoing]
  transfer_protocol = rsync_ssh
  control_file_extension = mistamover-ctrl-bss
  receipt_file_extension = mistamover-rcpt-bss
  thankyou_file_extension = mistamover-thanks-bss
  target_uses_arrival_monitor = True 
  retry_count = 3 
  receipt_file_poll_count = 100 
  receipt_file_poll_interval = 5 
  always_zip = False 
  dir_size_limit = 1000. 
  stop_file = .stop  
  stop_file_poll_interval = 600 
   
  [logging]
  base_log_dir = $(global:homedir)/mistamover/log
  log_level = INFO 
  port = 2000  
   
  [email]
  from = mistamover@localhost
  #threshold = ERROR 
  threshold = CRITICAL
  recipient = me@localhost
  subject = Error from MiStaMover 
  smarthost = localhost
   
  [rsync_ssh]
  transfer_mode = move
  cmd = /usr/bin/rsync 
   
  [disk_space_monitor]
  base_priority = 100
  # thresholds in MB - description in lib/DiskSpaceMonitor.py
  level_good = 1500
  level_low = 1000
  level_vlow = 500
  # note re poll_interval: 1GBit/s, maxed out, is 7.5GB/minute
  poll_interval = 60

The Data Stream Configuration File
----------------------------------
  
The data stream configuration file is called ``conf/dataset_my_outputs.ini`` and looks like::

  [data_stream]
  priority = 200
  name = my_outputs
  transfer_unit = file
  status = RUNNING
  directory = $(global:top)/outgoing/my_outputs
   
  [incoming]
  require_arrival_monitor = False
   
  [outgoing]
  target_host = localhost
  transfer_protocol = rsync_ssh
  # if this was True then rsync would run in mirror mode
  target_uses_arrival_monitor = False
  target_dir = $(global:top)/remote/my_outputs
   
  [rsync_ssh]
  username = ME 
  transfer_mode = mirror
  use_checksum = True
  check_size = True

The data stream configuration file can override any settings made in the global configuration file for the specific data stream of interest. The main settings that should be set for each data stream are:

 * ``name`` - the name of the data_stream
 * ``directory`` - where the data stream transfer process will monitor for files/directories that should be transferred
 * ``target_host`` - the full IP address or valid alias of the target machine that data will be transferred to
 * ``transfer_protocol`` - the protocol that will be used to transfer data to the target machine
 * ``target_dir`` - the directory on the target host where data should be transferred

See the :ref:`configuration` section for the full list of available settings. In the above example, the ``[outgoing]`` section sets the ``transfer_protocol`` to ``rsync_ssh``. This implies that there must be a section in the data stream (or global) configuration file called ``[rsync_ssh]`` that provides further details as required.

Once you have created a global configuration file and at least one data stream configuration file you are ready to run MiStaMover. As stated above, the tool can be invoked at the command-line as follows:

If you wish to run MiStaMover with a test dataset please see the section on :ref:`config_test_data`.

Example Data Stream Configuration files
---------------------------------------

The best way to get started is to copy and modify the :ref:`example_configs`.

Adding a new MiStaMover Data Stream
-----------------------------------

A MiStaMover data stream corresponds to a configuration file that instructs the main MiStaMover process to start a separate process that monitors a directory for incoming files/directories and transfers them on to a target directory on a remote (or local) server. 

New data streams can be added without stopping MiStaMover. The global configuration file is regularly re-scanned by the main process and the "data_stream_list" is read. If a new data stream name appears in the list then MiStaMover will look for the associated configuration file and will then start a new process for that specific Data Stream.

See the :ref:`configuration` section for more details about configuring a new data stream.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

