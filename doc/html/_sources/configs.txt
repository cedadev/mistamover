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

The following is an example of aglobal config file::  

  #  
  # Global config file - can override values per data_stream by giving them the 
  # same section and key in the data_stream config file                                          
  #                                                                                                                        
  [global]  
  # global section is intended for stuff which is unlikely to be overridden   
  # per-data_stream (although technically there is nothing to prevent a 'global'  
  # section in the data_stream config file)  
                                                                                                  
  debug_on = True                                                                    
  homedir = /home/users/mistamover                                                             
  #                                                                                            
  # the location of stager                                                              
  #                                                                                                      
  top = /home/users/jhorton/Download/SVN/jah/19mar2012  
  base_data_dir = $(global:top)/data                                                               
  #                                                                                               
  # the location of the global and data_stream config files  
  #                                                                                              
  config_dir = $(global:top)/conf                                                              
  # Note that data_stream_config_dir overrides data_stream_list in terms of where to look for config files 
  base_incoming_dir = /home/users/mistamover/incoming/                   
  #                                                                                              
  # a list of data_streams to transfer - each one of these will have a config file                  
  #                                                                                                
  data_stream_list = rsync_ssh                                                                     
  general_poll_interval = 3                                                                      

  [incoming]
  require_arrival_monitor = False
  control_file_extension = stager-ctrl-bss
  thankyou_file_extension = stager-thanks-bss
  stop_file = .stop                          

  [outgoing]
  #         
  # the transfer_protocol defines the underlying protcol used to transfer files
  # each protocol is wrapped in a class that inherits from TransferModules::TransferBase
  #                                                                                     
  transfer_protocol = rsync_ssh                                                         
  #                                                                                     
  # The transfer_mode can be either move OR mirror for rsync (all other protocols only support move)
  #                                                                                                 
  transfer_mode = move                                                                              

  control_file_extension = stager-ctrl-bss
  receipt_file_extension = stager-rcpt-bss
  thankyou_file_extension = stager-thanks-bss
  #                                          
  # by setting the arrival monitor to True - we use the overlaying handshake protcol
  # to ensure that files arrive at their destination  correctly                     
  #                                                                                 
  #target_uses_arrival_monitor = True                                               
  retry_count = 3                                                                   
  receipt_file_poll_count = 100                                                     
  receipt_file_poll_interval = 5                                                    
  dir_size_limit = 1000.                                                            
  stop_file = .stop                                                                 
  stop_file_poll_interval = 10                                                      

  [logging]
  #        
  # location of log files - this directory must exist
  #                                                  
  base_log_dir = /tmp/log                            
  log_level = INFO                                   
  #log_level = DEBUG                                 
  port = 2000                                        

  [email]
  #      
  # any log message of type CRITICAL or above will be emailed as well as logged
  #                                                                            
  from = badc@rl.ac.uk
  threshold = CRITICAL
  recipient = mistamover@stfc.ac.uk
  subject = Error from Local Stager
  smarthost = outbox.rl.ac.uk

  [disk_space_monitor]
  base_priority = 100
  # thresholds in MB - description in DiskSpaceMonitor.py
  level_good = 1500
  level_low = 1000
  level_vlow = 500
  # note re poll_interval: 1GBit/s, maxed out, is 7.5GB/minute
  poll_interval = 60

  ## A default data_stream priority can be set here as the data_stream config will fall
  ## back to the global config in the ordinary way.  But if not then the base
  ## priority will also be used as a default.
  # [data_stream]
  # priority = 100

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
  name = ftp
  transfer_unit = file
  status = RUNNING
  deletion_enabled = False
  #
  # location of files to transfer for this data_stream
  #
  directory = /home/users/mistamover/outgoing/my_data_stream
  
  [incoming]
  require_arrival_monitor = False
  
  [outgoing]
  #
  # the host we are transfering files to
  #
  target_host = cmip-dev1
  #
  # the underlying protocol we are using to transfer files
  #
  transfer_protocol = ftp
  target_uses_arrival_monitor = True
  #
  # the location on the target_host where we are placing the files
  #
  target_dir = /home/users/mistamover/incoming/my_data_stream
  
  [ftp]
  cmd = /usr/bin/ftp
  username = mistamover
  password = mistamover

Here is an example of the Data Stream config file that will run on the other server (that uses use Arrivals monitor)::

  [data_stream]
  priority = 200
  name = arrival_monitor
  transfer_unit = file
  status = RUNNING
  deletion_enabled = False
  #
  # location of files to transfer for this data_stream
  #
  directory = /home/users/mistamover/incoming/my_data_stream
  
  [incoming]
  require_arrival_monitor = True
  
  [outgoing]
  #
  # the host we are transfering files to
  #
  target_host = cmip-dev1
  #
  # the underlying protocol we are using to transfer files
  # - it is none as we are only listening for incoming files
  #
  transfer_protocol = none

Here is an example of a Data Stream config file that uses rsync ssh to mirror::

  [data_stream]
  priority = 200
  name = rsync_ssh
  transfer_unit = file
  status = RUNNING
  directory = /home/users/mistamover/outgoing/rsync_ssh
  
  [incoming]
  require_arrival_monitor = False
  
  [outgoing]
  target_host = cmip-dev1
  transfer_protocol = rsync_ssh
  target_dir = /home/users/mistamover/incoming/rsync_ssh
  
  [rsync_ssh]
  username = mistamover
  cmd = /usr/bin/rsync
  transfer_mode = mirror
 
Here is an example of a Data Stream config file that uses rsync native to move::

  [data_stream]
  priority = 200
  name = rsync_native
  transfer_unit = file
  status = RUNNING
  #
  # location of files to transfer for this data_stream
  #
  directory = /home/users/mistamover/outgoing/rsync_native
  
  [incoming]
  require_arrival_monitor = False
  
  [outgoing]
  #
  # the host we are transfering files to
  #
  target_host = cmip-dev1
  #
  # the underlying protocol we are using to transfer files
  #
  transfer_protocol = rsync_native
  target_uses_arrival_monitor = False
  #
  # the location on the target_host where we are placing the files
  #
  target_dir = Example/incoming/rsync_native
  
  [rsync_native]
  username = mistamover
  password = mistamover
  use_checksum = True
  check_size = True
  transfer_mode = move
  cmd = /usr/bin/rsync

Here is an example of Data Stream config file that uses gridftp to move::

  [data_stream]
  priority = 200
  name = gridftp
  transfer_unit = file
  status = RUNNING
  deletion_enabled = False
  #
  # location of files to transfer for this data_stream
  #
  directory = /home/users/mistamover/outgoing/gridftp
  
  [incoming]
  require_arrival_monitor = False
  
  [outgoing]
  #
  # the host we are transfering files to
  #
  target_host = mercury
  #
  # the underlying protocol we are using to transfer files
  #
  transfer_protocol = gridftp
  target_uses_arrival_monitor = False
  #
  # the location on the target_host where we are placing the files
  #
  target_dir = /disks/almond1/mistamover/incoming/gridftp
  
  [gridftp]
  username = mistamover
  cmd = /home/users/mistamover/globus/bin/globus-url-copy
  port = 2811
  proxy = myproxy.ceda.ac.uk
  username = mistamover
  password = mistamover


Configuration Options
---------------------

Here we define the sections that are defined in the configuration files and the options that can be set for each.

The sections can be as follows\:

**[global]**
  Intended for options that are unlikely to be overridden

**[data_stream]**
  Options required to define a data_stream - typically one section per data_stream config file

**[incoming]**
  Options required to define how MiStaMover will operate if it is acting as a server and receiving files (and using an Arrivals Monitor)

**[outgoing]**
  Options required to define how MiStaMover will operate when it pushes data to another computer

**[logging]**
  Options required to define where log files are kept etc.

**[email]**
  Options required to define who to send email to and what smarthost to use etc.

**[disk_space_monitor]**
  Options to define when to remove transfered files if disk space if getting low

**[rsync_ssh]**
  Options to define how rsync over ssh transfer module operates

**[rsync_native]**
  Options to define how native rsync transfer module operates

**[ftp]**
  Options to define how ftp transfer module operates

**[gridftp]**
  Options to define how gridftp transfer module operates

**[rsync_ssh]**
  Defines settings required for using the rsync-over-SSH transfer protocol.

*  `For each section, the following settings, their meanings and possible values are given below\:`

**[global]**
  debug_on
    If True, then debug will be written to the console

  homedir
    The user homedir

  top
    The location of MiStaMover

  base_data_dir
    The location of where data files will be located

  config_dir
    The location of the global and data_stream config files

  base_incoming_dir
    Location where incoming files will be stored

  data_stream_list
    List of datastreams which are being transfered

  general_poll_interval
    Interval (in seconds) at which MiStaMover polls for state changes

**[data_stream]**
  priority
    priority of data_stream - used if disk space monitor is used and disk space is low. It is used to determine if files from the data_stream should be deleted to make more space

  name
    name of data_stream

  directory
    location of files for this data_stream

  status
    status of data_stream, can be RUNNING or STOPPED

**[incoming]**
  require_arrival_monitor
    If True, then MiStaMover will run the Arrivals Monitor protocol for incoming data

  control_file_extension
    Defines file extensions used by Arrivals Monitor protocol

  receipt_file_extension
    Defines file extensions used by Arrivals Monitor protocol
  
  thankyou_file_extension
    Defines file extensions used by Arrivals Monitor protocol

  stop_file
    The name of the file that will stop any remote MiStaMover instances from sending more data to this MiStaMover Instance

**[outgoing]**
  target_uses_arrival_monitor
    If True, then MiStaMover will push data and expect the Arrivals Monitor protocol to be running on the target host

  target_host
    Eefines the host MiStaMover is pushing data to

  transfer_protocol
    Defines the TransferModule that will be used to push data to the target host

  target_dir
    Defines where on the target host the data will be pushed to

  control_file_extension
    Defines file extensions used by Arrivals Monitor protocol

  receipt_file_extension
    Defines file extensions used by Arrivals Monitor protocol  

  thankyou_file_extension
    Defines file extensions used by Arrivals Monitor protocol

  retry_count
    The number of times MiStaMover will retry a data push

  receipt_file_poll_count
    When usin gArrivals Monitor protocol - defines how many times a receipt for the data push will be requested before failing

  receipt_file_poll_interval
    When usin gArrivals Monitor protocol - defines how long to wait (in seconds) before requesting a receipt for the data push

  dir_size_limit
    The directory size limit for files that are being pushed

  stop_file
    The name of the file that will stop MiStaMover from sending more data to the remote  MiStaMover Instance

  stop_file_poll_interval
    The interval at which MiStaMover polls the remote host for the presence of a stop file

**[logging]**
  base_log_dir
    The location of log files

  log_level
    The minimum log level (of a message) before it is logged to file

  port
    The port on which the log server listens

**[email]**
  from
    The email address that should be used for any emails sent by MiStaMover

  threshold
    The minimum level (of a message) before it is sent via email

  recipient
    The email address to whom the emails should be sent

  subject
    The subject line of emails sent from MiStaMover

  smarthost
    The smarthost that should be used in the email transfer

**[disk_space_monitor]**
  base_priority
    priority to define a baseline as to whether or not to remove transfered files if disk space is getting low

  level_good
    An integer value defining (in Mb) how much disk space is considered 'good'

  level_low
    An integer value defining (in Mb) how much disk space is considered 'low'

  level_vlow
    An integer value defining (in Mb) how much disk space is considered 'vlow'

  poll_interval
    The interval at which the disk space monitor will check disk space levels

**[rsync_ssh]**
  cmd
    The full-path to the command that will be run.
    
  transfer_mode
    Set the transfer mode to either ``move`` or ``mirror``.

  checksum
    If True then rsync will use checksum to determine if file needs to be transfered

  size-only
    If True then rsync will use size only to determine if file needs to be transfered

**[rsync_native]**
  cmd
    The full-path to the command that will be run

  username
    Username to use in authentication during transfer

  password
    Password to use in authentication during transfer

  transfer_mode
    Set the transfer mode to either ``move`` or ``mirror``

**[ftp]**
  cmd
    The full-path to the command that will be run

  username
    Username to use in authentication during transfer

  password
    Password to use in authentication during transfer

**[gridftp]**
  cmd
    The full-path to the command that will be run

  username
    Username to use in authentication during transfer

  password
    Password to use in authentication during transfer

  port
    Port of GridFtp server on remote host

  proxy
    location of MyProxy proxy server (used to serve credentials)


Extensions to the Standard Configuration File Parsing
-----------------------------------------------------

In addition to supporting the INI file format understood by the python ``ConfigParser`` standard module we have also enabled a find-and-replace option based on the following syntax: 

  ``$(section:option)``
 
This allows you to re-use values that are set elsewhere in the configuration file (or the global configuration file). For example::

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





