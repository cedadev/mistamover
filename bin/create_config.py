#!/usr/bin/env python
"""
create_config.py
================

Script to generate configuration files for mistamover. 

To create the global configuration file use:

    bin/create_config.py -t global <settings>

To create a data stream configuration file use:

    bin/create_config.py -t <transfer_method> <settings>

To view this message use:

    bin/create_config.py -h

To view the list of settings that must be defined for a specific configuration use:

    bin/create_config.py -h <config_type>

Where:

    <settings>     - is a list of settings to add to the configuration file formatted as:
                         <section>:<name>=<value>
                     <section> is the section of the configuration file (shown as "[<section>]")
                     <name> and <value> are options set within a section of the configuration file,
                     shown as: <name> = <value>
    <transfer_method> - is the transfer method, such as "rsync_ssh", "ftp", "rsync_native", "gridftp_myproxy"
    <config_type>     - is either "global" or a transfer method (see <transfer_method> above)

Example usage
=============

Global configuration file:

 $ bin/create_config.py -t global global:config_dir=/data/datawriter/mistamover/conf "global:data_stream_list=dataset_1 model_data" logging:base_log_dir=/data/datawriter/logs email:from=me.you@themorus.gov.uk email:recipient=me.you@themorus.gov.uk

Data stream configuration file:

 $ bin/create_config.py -t rsync_ssh data_stream:name=dataset_1 rsync_ssh:username=datawriter outgoing:target_host=100.100.200.100 outgoing:target_dir=/data/staging_area/dataset_1

"""


# Standard library imports
import os, sys

# Global variables
template_dir = "templates"
config_dir = "conf"

known_configs = [f.split(".")[0] for f in os.listdir(template_dir)]

def gatherMinimumRequirementsForConfig(tmpl):
    "Reads template and returns a list of required settings as [(key, value)]."
    reqs = []

    for line in open(tmpl):
        if line.strip() == "" or line[0] == "#":
            pass
        elif line[0] == "[":
            section = line[1:].split("]")[0]
        else:
            equ = line.find("=")
            if equ < 0:
                raise Exception("Unrecognisable line in config template: '%s'" % line)

            option = line[:equ].rstrip()
            value = line[equ + 1:].strip()

            if value == "__MUST_DEFINE__":
                reqs.append((section, option)) 

    return reqs


def showHelpForConfig(conf_type):
    if conf_type not in known_configs:
        raise Exception("Unknown config type provided: '%s'" % conf_type)


    print "HELP on requirements for setting up a configuration file of type: %s\n" % conf_type
    print "You need to define:"
  
    tmpl = getFilePaths(conf_type, tmpl_only = True)[0]
    config_minimal_requirements = gatherMinimumRequirementsForConfig(tmpl)

    for k, v in config_minimal_requirements:
        print "\t%s:%s" % (k, v)

    print "\nTry something like:\n"
    print " $ bin/create_config.py -t %s" % conf_type,

    for k,v in config_minimal_requirements:
        print "%s:%s=SOMETHING" % (k, v),


def getFilePaths(conf_type, tmpl_only = False, **args):
    """
    Returns tuple of (template_file, config_file) to be read and written.
    If ``tmpl_only`` is True then return (template_file, None). 
    """
    conf = None

    if conf_type == "global":
        tmpl = os.path.join(template_dir, "global.tmpl")
        if tmpl_only == False: conf = os.path.join(config_dir, "NEWglobal.ini")
    else:
        name = args.get("data_stream:name")
        if not name:
            raise Exception("Must define 'data_stream:name=<value>' in data stream config arguments.")

        tmpl = os.path.join(template_dir, "%s.tmpl" % conf_type)
        if tmpl_only == False: conf = os.path.join(config_dir, "ds_%s.ini" % name)

    if not os.path.isfile(tmpl):
        raise Exception("Configuration template file '%s' does not exist for configuration type '%s'" % (tmpl, conf_type))

    return (tmpl, conf)
    

def createConfig(conf_type, **args):
    """
    Creates configuration file of type ``conf_type`` which is either "global" or
    a transfer method such as "rsync_ssh" or "ftp".

    ``args`` are settings to add to the new configuration file formatted as:
            <section>:<name>=<value>
    Where:
            <section> is the section of the configuration file (shown as "[<section>]")
            <name> and <value> are options set within a section of the configuration file,
                     shown as: <name> = <value>

    """ 
    if conf_type not in known_configs:
        raise Exception("Unknown config type provided: '%s'" % conf_type)

    (tmpl, conf) = getFilePaths(conf_type, **args) 

    input = open(tmpl)
    output = []

    section = None

    for line in input:
        line = line.strip()
       
        if line == "" or line[0] == "#":
            pass
        elif line[0] == "[":
            section = line[1:].split("]")[0]
        else:
            equ = line.find("=")
            if equ < 0:
                raise Exception("Unrecognisable line in config template: '%s'" % line)

            option = line[:equ].rstrip()
            value = line[equ + 1:].lstrip()  
            
            combined = "%s:%s" % (section, option)
            if combined in args.keys():
                line = "%s = %s" % (option, args[combined])
            elif value.strip() == "__MUST_DEFINE__":
                raise Exception("Please define the setting: '%s=<value>' at the command line." % combined)
                
        output.append(line)

    # Open and write new config file
    if os.path.isfile(conf):
        os.chmod(conf, 0640)
        os.remove(conf)

    f = open(conf, "w")
    for l in output:
        f.write("%s\n" % l)
   
    f.close()
    os.chmod(conf, 0400)
    print "Wrote: %s" % conf


def parseArgs(arg_list):
    "Parses the arguments list and calls appropriate function (or prints advice and exits."
    if len(arg_list) < 2:
        print __doc__ 
        print "\nArguments must start with '-t <config_type>' or '-h <config_type>'."
        sys.exit()

    if arg_list[0] == "-h":
        showHelpForConfig(arg_list[1])
        sys.exit()

    if arg_list[0] != "-t" or len(arg_list) < 2:
        print "First argument must be '-t <config_type>'."
        sys.exit()

    conf_type = arg_list[1]
    args = {}

    for arg in arg_list[2:]:
        key,value = arg.split("=")
        args[key] = value

    return (conf_type, args)

def main(args):
    "The main controlling function."
    (conf_type, arg_dict) = parseArgs(args)

    createConfig(conf_type, **arg_dict)    


if __name__ == "__main__":

    args = sys.argv[1:]
    main(args)

