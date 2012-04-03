.. _configuration:

Configuring MiStaMover
======================

**MiStaMover** is told how to run, where to run and what to run by a set of configuration files. The format is based on the Python INI file format [REF: TOFIX], with a few extensions.

The most important of configuration files is the:

 * Global Configuration File

This defines the global information MiStaMover needs and also sets up defaults for items defined in the:

 * Data Stream Configuration Files

These define such information as what a data stream is called, where its data can be found on arrival, which protocol should be used to transfer the data and the address of the remote host that data should be forwarded to.

Global Configuration Files
--------------------------

TBC

Data Stream Configuration Files
-------------------------------

The following is an example of a data stream-specific configuration file. It contains information for the `mytest` Data Stream::

  [data_stream]
  name = mytest
  status = RUNNING
  completion_file = thatsallfolks
  priority = 50

  [incoming]
  require_arrival_monitor = False

  [outgoing]
  control_file_extension = ctrl12
  receipt_file_extension = rcpt12
  transfer_protocol = ftp
  target_host = localhost
  target_dir = /xfers/incoming/mytest2
  target_uses_arrival_monitor = True
  receipt_file_poll_count = 5
  receipt_file_poll_interval = 1
  #stop_file_poll_interval = 5

  [ftp]
  #username = .....
  #password = ......

  [email]
  recipient = simon.diming@diming-froim.com

The various sections and options in the configuration file are explained in detail below:

data_stream
-----------

name

  The name of the data_stream

.. _example_configs:

Example Configuration Files
---------------------------

The following example configuration files can be copied and modified as you require. It is easier to start with these than to build new files from scratch. The examples are\:

 * Global configuration example
 * Rsync-over-SSH data stream "move" example
 * Rsync-over-SSH data stream "mirror" example
 * Rsync-native data stream "move" example
 * GridFTP data stream "move" example
 * FTP data stream "move" example (no arrivals monitor)
 * FTP data stream "move" example (with arrivals monitor)
 
**TBC - need to cover all the above examples in section below!!!**

Here is an example of a *one-off* config file that uses the ``rsync-over-ssh`` transfer protocol::

  #                                                                
  # Global oneshot config file - can override values per data stream by giving them the 
  # same section and key in the data stream config file                                 
  #                                                                                 

  [global]
  # global section is intended for stuff which is unlikely to be overridden
  # per-data stream (although technically there is nothing to prevent a 'global'
  # section in the data stream config file)                                     

  homedir = /home/users/jhorton
  top = /home/users/jhorton/Download/SVN/jah/jah
  base_data_dir = $(global:top)/data               
  config_dir = $(global:top)/conf                     
  base_incoming_dir = /home/users/jhorton/Download/SVN/jah/incoming                               
  data_stream_list = jah3                                                                             
  general_poll_interval = 1                                                                       

  [data_stream]
  priority = 200
  name = jah3      
  transfer_unit = file
  status = RUNNING    
  directory = /home/users/jhorton/Download/SVN/jah/outgoing/jah3

  [incoming]
  require_arrival_monitor = False
  control_file_extension = mistamover-ctrl-bes
  thankyou_file_extension = mistamover-thanks-bes
  stop_file = .stop                          

  [outgoing]
  target_host = cmip-dev2
  target_dir = /home/users/jhorton/incoming/jah
  transfer_protocol = rsync                    
  control_file_extension = mistamover-ctrl-bss     
  receipt_file_extension = mistamover-rcpt-bss     
  thankyou_file_extension = mistamover-thanks-bss  
  target_uses_arrival_monitor = False          
  retry_count = 3                              
  receipt_file_poll_count = 100                
  receipt_file_poll_interval = 5               
  always_zip = False                           
  dir_size_limit = 1000.                       
  stop_file = .stop                            
  stop_file_poll_interval = 600                

  [logging]
  base_log_dir = /tmp/log                                          
  log_level = INFO                                                 
  port = 2000                                                      

  [email]
  from = badc@rl.ac.uk
  threshold = CRITICAL
  recipient = john.horton@stfc.ac.uk
  subject = Error from Local MiStaMover 
  smarthost = outbox.rl.ac.uk       

  [rsync]
  username = jhorton
  transfer_mode = move
  cmd = /usr/bin/rsync     

  [disk_space_monitor]
  base_priority = 100
  # thresholds in MB - description in DiskSpaceMonitor.py
  level_good = 1500
  level_low = 1000
  level_vlow = 500
  # note re poll_interval: 1GBit/s, maxed out, is 7.5GB/minute
  poll_interval = 60

Here is an example of a Data Stream config file the uses FTP and an Arrivals Monitor::

  [data_stream]                                                                                           
  priority = 200                                                                                      
  name = jah                                                                                          
  transfer_unit = file                                                                                
  status = RUNNING                                                                                    
  directory = /home/users/jhorton/Download/SVN/jah/outgoing/jah                                       

  [incoming]
  require_arrival_monitor = False

  [outgoing]
  target_host = cmip-dev1
  transfer_protocol = ftp
  target_uses_arrival_monitor = True
  target_dir = /home/users/jhorton/incoming/jah

  [ftp]
  cmd = /usr/bin/ftp
  username = jhorton
  password = password


Here is an example of the Data Stream config file that will run on the other server (that uses use Arrivals monitor)::

  [data_stream]                                                                                                                 
  priority = 200                             
  name = jah                             
  transfer_unit = file                   
  status = RUNNING                       
  directory = /home/users/jhorton/incoming/jah

  [incoming]
  require_arrival_monitor = True

  [outgoing]
  target_host = cmip-dev2
  transfer_protocol = none
  target_uses_arrival_monitor = False
  target_dir = /home/users/jhorton/incoming/


Here is an example of a Data Stream config file that uses rsync to mirror::

  [data_stream]        
  priority = 200   
  name = jah2      
  transfer_unit = file
  status = RUNNING 
  directory = /home/users/jhorton/Download/SVN/jah/outgoing/jah2                                      

  [incoming]
  require_arrival_monitor = False

  [outgoing]
  target_host = mercury
  transfer_protocol = rsync
  target_uses_arrival_monitor = False
  target_dir = /disks/almond1/jhorton/jah2

  [rsync]
  username = jhorton
  transfer_mode = mirror
  cmd = /usr/bin/rsync
  
Configuration Options
---------------------

Here we define the sections that are defined in the configuration files and the options that can be set for each.

The sections can be as follows\:

ADDMORE

**``[rsync_ssh]``**
  Defines settings required for using the rsync-over-SSH transfer protocol.

For each section, the following settings, their meanings and possible values are given below\:

**``[rsync_ssh]``**
  cmd
    The full-path to the command that will be run.
    
  transfer_mode
    Set the transfer mode to either ``move`` or ``mirror``.
  
Extensions to the Standard Configuration File Parsing
-----------------------------------------------------

In addition to supporting the INI file format understood by the python ``ConfigParser`` standard module we have also enabled a find-and-replace option based on the following syntax: 

  ``$(section:option)``
 
This allows you to re-use values that are set elsewhere in the configuration file (or the global configuration file???CHECK???TOFIX???TRUE???). For example::

  [global]
  homedir = /home/users/me 
  top = /home/users/me/work 
  base_data_dir = $(global:top)/data
  config_dir = $(global:homedir)/mistamover/conf  
  
Would substitute the value of "/home/users/me" for the string "$(global:homedir)".

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`





