.. _modes:

Running Modes
=============

As mentioned in the :ref:`intro`, there are a number of modes in which MiStaMover can be run. This section describes them in more detail.

The 4 main running modes are:
 
 #. One-off mirror
 #. One-off move
 #. Daemon mirror
 #. Daemon move
 
One-off mirror mode
-------------------

Running MiStaMover as a *one-off* process means that it will scan the incoming directory for each data stream specified only once. If it finds files or directories during that scan it will transfer those to the target host. Once it has completed this task for all data streams it will exit.

The use of the *mirror* transfer mode instructs the tool to copy the entire contents of the incoming directory to the target host *without* deleting the contents in the incoming directory.

**NOTE that the *mirror* transfer mode is only compatible with the `rsync_ssh` and `rsync_native` transfer protocols.**

If sub-directories exist within the incoming directory then MiStaMover will either mirror these as they are (if the transfer protocol uses *rsync*) or zip up each directory and transfer the zip file.

One-off move mode
-----------------

The *one-off* process can also be run in *move* transfer mode. In this case it acts the same as the one-off *mirror* mode but after each file is successfully transferred to the target host **the copy on the local host will be deleted.**

**WARNING: The default transfer mode is "move". Do not set your incoming directory to a location in which you intend to keep data without setting the transfer mode to "mirror"!** 

Daemon mirror mode
------------------

Running MiStaMover as a *daemon* process essentially runs as an eternal loop around the *one-off* process. Each time a set of files and/or directories have been transferred the incoming directory will be re-scanned and the process repeated. If nothing is found in the incoming directory then the process will pause for a while (as configured in the ``pause_time:TOFIX`` setting) and then re-scan.

Running as a *daemon* process with *mirror* transfer mode will continue to mirror the contents of the incoming directory (for each data stream) to the target host so it can be left running if an ongoing mirror or backup strategy is required. Modifying the ``pause_time:TOFIX`` setting allows the pause time between re-scanning and mirroring to be modified.

Daemon move mode
----------------

Running as a *daemon* process in *move* transfer mode will continue to push data from the incoming directory of each data stream and delete the local copy once it has been successfully transferred. Each time a set of files and/or directories have been transferred the incoming directory will be re-scanned and the process repeated. In this way, MiStaMover can be configured to act as a *staging tool* that monitors a number of directories for new data and pushes it on to a range of target host machines as required.

**WARNING: The default transfer mode is "move". Do not set your incoming directory to a location in which you intend to keep data without setting the transfer mode to "mirror"!** 
