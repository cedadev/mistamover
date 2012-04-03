.. _intro:

Introduction
============

What does **MiStaMover** do?
----------------------------

**MiStaMover** is an open-source python-based tool that aims to simplify the transfer of large datasets between remote servers. As the name indicates, MiStaMover is able to **Mirror, Stage and Move data**. The tool was developed to support the UK academic research community manage its data effectively between key institutions, computing sites and data centres. But hopefully it can help anyone with a need to mirror, stage or move files.
 
MiStaMover is typically used in the following ways:

 * Running a *one-off* transfer of a set of data files from a source server to a target server
 * As a *daemon* process controlled by an administrator that allows multiple :ref:`Data Streams <data_stream>` to be :ref:`Moved <move>` or :ref:`Mirrored <mirror>` to remote servers based on configuration information.
 
See the :ref:`modes` for a full list of running modes.

MiStaMover is able to manage multiple transfer processes in a manner than ensures what is sent from the :ref:`Source Host <source_host>` actually arrives in-tact on the :ref:`Target Host <target_host>`.  

The following features and functionality are included:

 #. Able to run as a daemon or a one-off process
 #. Each Data Stream is managed by single configuration file
 #. Files and/or directories can be recieved and sent by various transfer protocols (such as :ref:`rsync`` and :ref:``ftp``)
 #. Transfer failures will be re-tried based on a configuration setting
 #. Full logging of all transfers
 #. An alert feature that will highlight any failures or issues via e-mail
 #. Monitoring of available disk space
 #. For each Data Stream, a ``.stop`` file can be used to suspend a transfer process
 #. The integrity of incoming data can be checked by the use of control files and calculation of checksums
 #. Once configured, **MiStaMover** will run automatically with no manual interaction
 
Why build another transfer tool?
--------------------------------

MiStaMover is not creating a new protocol or method of moving data around the networks. We believe that there are enough tools and protocols already. The main purpose of the tool is to provide a generic, flexible and robust framework that can allow system administrators, data managers and scientists to move and mirror data effectively around the wide area network.

By building in Python the tool is easy to install, configure and extend. The functionality provided should allow users to set the transfer running and to walk away without having to continually monitor that the process is running correctly.

Who should use stager?
----------------------

MiStaMover is most likely to be used by:

 * System Administrators: setting up a :ref:`MiStaMover Service <mistamover_service>` that allows multiple users to move and mirror their data to a range of remote hosts.
 * Data Managers: running ongoing or large one-off transfers around between computing and archival sites.
 * Users: individual linux users that need to reliably move or mirror data between sites.
   
Can I get a copy of **MiStaMover**?
-----------------------------------

**MiStaMover** is available under an open-source licence so anyone can have a copy. See the :ref:`getting_started` for how to access the source, install and configure MiStaMover.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

