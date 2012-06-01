#!/usr/bin/env python                                                                 
"""                                                                                   
create_config.py                                                                      
================                                                                      

Script to generate configuration files for mistamover. 

To create the global configuration file use:

    bin/create_config.py -t <config_type>

    where config_type is 
    global


o create a data stream configuration file use

    bin/create_config.py -t <config_type> <unique_name>

    where config_type is one of
    rsync_ssh
    rsync_native
    ftp
    gridftp_myproxy
    gridftp_certificate


o view the list of settings that must be defined for a specific configuration use:

    bin/create_config.py -h <config_type> <unique_name>

    where config_type is one of those defined above


To view this message use:

    bin/create_config.py -h


Example usage
=============

Global configuration file:

$ bin/create_config.py -t global

Data stream configuration file:

 $ bin/create_config.py -t rsync_ssh dataset_1

"""

# Standard library imports
import os, sys, stat 

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


def showHelpForConfig(conf_type, name):
    if conf_type not in known_configs:
        raise Exception("Unknown config type provided: '%s'" % conf_type)


    print "HELP on requirements for setting up a configuration file of type: %s\n" % conf_type
    print "You need to define:"

    tmpl = getFilePaths(conf_type, name, tmpl_only = True)[0]
    config_minimal_requirements = gatherMinimumRequirementsForConfig(tmpl)

    for k, v in config_minimal_requirements:
        if v == "name":
            print "\t%s:%s (eg. %s)" % (k, v, name)
        else:
            print "\t%s:%s" % (k, v)


def parseArgs(arg_list):
    "Parses the arguments list and calls appropriate function (or prints advice and exits."
    if len(arg_list) < 2:
        print __doc__
        print "\nArguments must start with '-t <config_type>' or '-h <config_type>'."
        sys.exit()

    if arg_list[0] == "-h" or arg_list[0] == "-t":
        if arg_list[1] == "global":
            name = "global"
        else:
            if len(arg_list) != 3:
                print "\nArguments must start with '-t <config_type> <unqiue_name>' or '-h <config_type> <unique_name>'."
                sys.exit()
            else:
                name = arg_list[2]
         
    if arg_list[0] == "-h":
        showHelpForConfig(arg_list[1], name)
        sys.exit()

    if arg_list[0] != "-t" or len(arg_list) < 2:
        print "First argument must be '-t <config_type>'."
        sys.exit()

    conf_type = arg_list[1]

    return (conf_type, name)



def getFilePaths(conf_type, name, tmpl_only = False):
    """                                                
    Returns tuple of (template_file, config_file) to be read and written.
    If ``tmpl_only`` is True then return (template_file, None).          
    """                                                                  
    conf = None                                                          

    if conf_type == "global":
        tmpl = os.path.join(template_dir, "global.tmpl")
        if tmpl_only == False: conf = os.path.join(config_dir, "NEWglobal.ini")
    else:                                                                      
        if not name:                                                           
            raise Exception("Must define 'data_stream:name=<value>' in data stream config arguments.")

        tmpl = os.path.join(template_dir, "%s.tmpl" % conf_type)
        if tmpl_only == False: conf = os.path.join(config_dir, "ds_%s.ini" % name)

    if not os.path.isfile(tmpl):
        raise Exception("Configuration template file '%s' does not exist for configuration type '%s'" % (tmpl, conf_type))

    return (tmpl, conf)


def createConfig(conf_type, name):
    """                             
    Creates configuration file of type ``conf_type`` which is either "global" or
    a transfer method such as "rsync_ssh" or "ftp".
    """
    if conf_type not in known_configs:
        raise Exception("Unknown config type provided: '%s'" % conf_type)

    (tmpl, conf) = getFilePaths(conf_type, name)

    input = open(tmpl)
    output = []

    #print conf_type, name, tmpl, conf

    fn = open(tmpl, 'r')
    flines = fn.readlines()
    fn.close()

    i = 0
    j = len(flines)
    section = None
    while i < j:
        fl = flines[i].strip()
        if fl.startswith('#'):
            print fl
            output.append(fl)
            i = i + 1
        elif fl.startswith('['):
            s1 = fl.replace('[', '')
            s2 = s1.replace(']', '')
            section = s2
            output.append(fl)
            #print "section = ", section
            i = i + 1
        elif len(fl) == 0:
            output.append(fl)
            i = i + 1
        elif not fl.startswith('#') and len(fl) != 0 and not fl.startswith('['):
            fls = fl.split()
            currvar = fls[0].strip()
            if len(fls) == 3:
                fls2 = fls[2].strip()
                if fls2 == "__MUST_DEFINE__":
                    s = ""
                    while len(s) == 0:
                        print "required :", section + ":" + fls[0].strip()
                        s = raw_input('--> ')
                    print "setting", section + ":" + currvar, "=", s, "\n"
                    line = currvar + " = " + s
                    output.append(line)
                else:
                    print "optional :", section + ":" + fls[0].strip(), "(press enter to accept default) :", fls[2].strip()  
                    s = raw_input('--> ')
                    if len(s) == 0:
                        print "setting", section + ":" + currvar, "=", fls2, "\n"
                        line = currvar + " = " + fls2
                        output.append(line)
                    else:
                        print "setting", section + ":" + currvar, "=", s, "\n"
                        line = currvar + " = " + s
                        output.append(line)
            if len(fls) == 2:
                print currvar, " : (optional : no default value currently set)"
                s = raw_input('--> ')
                print "setting", section + ":" + currvar, "=", s, "\n"
                line = currvar + " = " + s
                output.append(line)
            #print "fls = ", fls
            i = i + 1

    # write out output
    f = open(conf, "w")
    for l in output:
        f.write("%s\n" % l)

    f.close()
    os.chmod(conf, stat.S_IRUSR)
    print "Wrote: %s" % conf
 
def main(args):
    "The main controlling function."
    (conf_type, name) = parseArgs(args)
    createConfig(conf_type, name)

if __name__ == "__main__":
    args = sys.argv[1:]
    main(args)


