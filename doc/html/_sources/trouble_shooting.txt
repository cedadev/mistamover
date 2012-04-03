.. _trouble_shooting:

Trouble-shooting
================

This section provides help and explanations.

Frequently Asked Questions
--------------------------

Why does MiStaMover not run on Python 2.4 or older versions?
  We had to make a cut-off point and we decided that Python 2.5 and above was reasonable. MiStaMover may not run on older versions of Python.
  
Why is the "mirror" transfer mode only available for rsync transfer protocols?
  The `rsync` tool has been built to be able to exactly duplicate the contents of a directory to a remote host. This is a relatively complex function that would require significant coding to achieve with all transfer protocols. Within MiStaMover it has only therefore been possible to implement the "mirror" transfer mode as a thin wrapper around the existing functionality of rsync.
  
Why does MiStaMover not unzip directories once delivered to the target host?
  A number of transfer protocols are available to push data to a remote host. Since each protocol has its own limitations we could not implement a generic solution for pushing a directory structure that would work for all. As a result if the :ref:`rsync_ssh` or :ref:`rsync_native` protocols are used then an entire directory will be copied to the target host as is.
  
  However, for other protocols there is no direct support for remotely copying whole directories. We therefore took the decision to zip the directory on the source host so that we could verify the send process robustly. Unzipping on the target host would require a signficant amount of extra engineering which was considered out of scope for the development of this tool.
  


  
  