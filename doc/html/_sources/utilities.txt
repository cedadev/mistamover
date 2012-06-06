.. _utilities:

Utilities
=========

This section explains the various utilities that come with MiStaMover.

watch_rate
  Utility to interactively watch rate of disk usage change at a
  particular path (e.g. useful while copying data).

  Reports rate of disk usage over most recent poll interval and
  also average rate since start of running the program.

Usage::

  watch_rate [-f] [-i poll_interval] <path>

  options:
  -f   do a 'df' of the containing filesystem (defaults to du)
  -i poll_interval   - time in seconds between measurements (defaults to 5)

  (hint: do not set poll interval too short when using du)



gridftp.py
  A wrapper script for using gridftp

runCommand.py
  A module that allows commands to be run from python

create_config.py
  A script that is used to create config files for MiStaMover. Documentation can be found in the :ref:`create_config` page
