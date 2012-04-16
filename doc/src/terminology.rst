.. _terminology:

Terminology
===========

This section explains the meaning of various terms used in relation to MiStaMover.

.. daemon:

**Daemon**
  Running MiStaMover as a *daemon* process will continue to scan incoming directory and then transfer the files/directories found. It will repeat this until the process is interrupted.
  
.. _data_stream:

**Data Stream**
  A *data stream* is the set of files and/or directories that are found in the `Source Directory` on the local host that are *moved* or *mirrored* to the target host.
 
.. _move:
 
**Move**
  To *move* a file/directory is a three-stage process: (1) the file/directory is copied to the *target host*; (2) the success of the delivery is verified and (3) the source copy is deleted.

.. _mirror:
  
**Mirror**
  The *mirroring* of a file/directory on the local host involves duplicating it exactly on the *target host*.
  
.. _source_host:
  
.. _one_off:

**One-off**
  Running MiStaMover as a *one-off* process will scan each data stream incoming directory only once, transfer the files/directories found, and then exit.
  
**Source Host**
  The *source host* is the local server on which the MiStaMover process is running: monitoring incoming directories and *moving* or *mirroring* the contents to a *target host*.

.. _target_host:
  
**Target Host**
  The *target host* is the remote server that the *source host* makes contact with and either *moves* or *mirrors* files to.
  
.. _transfer_mode:

**Transfer Mode**
  The *transfer mode* can be set in the configuration files as either `move`_ or `mirror`_.

**Incoming**
  The directory where files are received to

**Outgoing**
  The directory where files are pushed from
