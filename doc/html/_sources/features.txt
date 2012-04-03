.. _features:

Advanced Features
=================

How to suspend transfers for a data_stream
--------------------------------------

``MiStaMover`` uses the notion of a ``.stop`` file to inform the the transfer handler to stop doing anything. This behaves as follows:

1. A file called ``.stop`` is placed (manually or otherwise) in the dataset transfer directory.
2. ``MiStaMover`` knows that it should not attempt to transfer any files until the ``.stop`` file has been removed.
3. A remote deliverer can poll for this file to find out whether to send data.
4. A remote deliverer can also send ``.stop`` file itself in order to instruct ``MiStaMover`` to stop sending files.
5. A remote deliverer can also remove the ``.stop`` file itself to instruct ``MiStaMover`` to resume transfers.


Note that the ``DiskSpaceMonitor`` class will create and delete ``.stop`` files in response to changes in the amount of disk space available. This only occurs when the disk is getting full, or very full. See the `DiskSpaceMonitor <modules/DiskSpaceMonitor.html>`_ documentation for more details.

How to change the priority of a data_stream
-------------------------------------------

The global.ini file defines an option in the ``disk_space_monitor`` section called ``base_priority``.

This is option will cause any incoming data_streams to be monitored and stopped (as described above) if disk space gets too low

Data_streams with priorities lower than the base_priority will be stopped (and potentially removed) before data_streams with higher priorities.

Data_streams will only be removed if the option in the ``data_stream`` section of the data_stream config file called ``deletion_enabled`` is set to ``True``


How to ensure data is transfered correctly (for protocols that do not do this already)
--------------------------------------------------------------------------------------

MiStaMover uses the concept of an Arrivals Monitor that can be switched on via the config files on a per dataset basis

 - By using an arrivals monitor, a file is pushed to a server along with a control file that defines the size and checksum of the file.
 - The remote server is also running a MiStaMover instance (and is using Arrivals Monitor) so, recevies and data and once it receives the control file, checksums the data file and if the size and checksum of the received file is correct (as defined by the control file) then the remote stage instance places a receipt file in the directory.
 - The initial 'push' instance of mistamover pulls the receipt file from the remote server and pushs a thank you file to the remote server which ends the transaction/
 - If for any reason the transfer failed, then the remote server places the appropriate rror code in the receipt file and the initial push mistamover instance re-pushes the data
 
.. _logging:
 
Logging
-------

MiStaMover is managed by a main process and a set of sub-processes, one per :ref:`Data Stream <data_stream>`. A separate logging process is started when you run MiStaMover that manages all the log files, as follows:

 * The main MiStaMover log file (``mistamover_ctl.log``)
 * A Data Stream Transfer Controller log file for each Data Stream (e.g.: ``dtc_proj1.log``)
 * A TransferModule log file for each Data Stream (e.g.: ``rsync_proj1.log``)
 * A Disk Space Manager log file (``dsm_local.log``)
 
All files are logged to the directory specified in the ``logging:base_log_dir`` configuration setting.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

