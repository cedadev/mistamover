.. _create_config:

create_config
=============

MiStaMover config files can be created using a template system and a script called `create_config.py` (which can be found in the MiStaMover `bin` directory)

This utility asks the user questions and the repsonses are used to generate a config file.

The config files generated will be placed in the MiStaMover `conf` directory

create_config.py can be used in the following way

To create the global configuration file use::

    bin/create_config.py -t <config_type>

    where config_type is 
    global               


To create a data stream configuration file use::

    bin/create_config.py -t <config_type> <unique_name>

    where config_type is one of
    rsync_ssh                  
    rsync_native               
    ftp                        
    gridftp_myproxy            
    gridftp_certificate        
    arrival_monitor

To view the list of settings that must be defined for a specific configuration use::

    bin/create_config.py -h <config_type> <unique_name>

    where config_type is one of those defined above


To view this message use::

    bin/create_config.py -h


Example usage::

  Global configuration file:

  $ bin/create_config.py -t global

  Data stream configuration file:

   $ bin/create_config.py -t rsync_ssh dataset_1

  Arguments must start with '-t <config_type>' or '-h <config_type>'.


