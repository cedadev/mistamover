# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Provides BaseConfig - a class that makes a config file act like a dictionary

    myconf = BaseConfig("myfile.ini")
    val = myconf["mysection"]["mykey"]

for each value you read, it tries to return int, failing this float,
failing this returns bool for special string values 'true' / 'false'
(case insensitive test), failing this returns string

added feature is that if the value does not exist in the config,
then you get None instead of an exception

Another added feature is that in any string value, you can have a substring
which is substituted using another variable, in the format
{{var:[section]key}}.
Substitutions also include other substitutions.  Documenting
by example:

    [mysection]
         topdir=/some/path

    [othersection]
         dir1={{var:[mysection]topdir}}/some/subdirectory
         dir2={{var:[othersection]dir1}}/bar

It is entirely the user's responsibility not to set up loops when doing this.

You can also have expression substitutions, in the format {{eval:python_code}}
e.g. {{eval:1+1}}.  These are evaluated with eval.  They do not have to return
a string type, although in that case they should be constitute the whole of the
value as otherwise there will be an error from concatenating a string with
another type.  Expression substitutions are evaluated after variable substitutions.

Another added feature is compulsory variables.  The presence of these variables
will be checked for at the time that the config is read, and an exception raised
if not.  The compulsory variable section is empty in this class, but may be
overridden to useful effect in a subclass.

Variables can be overridden via environment vars called
CONFIG__<section>__<key> e.g. in the example above setting
CONFIG__mysection__topdir=/some/other/path will override
any value in the file and will also find its way into any substitutions
"""

import ConfigParser
import sys
import os
import time
import re

import settings

class ConfigSection(dict):
    """
    A class to make a section act as a dictionary.
    This class is unlikely to be instantiated directly by calling code.
    """

    _varSubsRe = re.compile("\$\(([a-zA-Z_]+)\:(.*?)\)")
    _evalSubsRe = re.compile("\{\{eval:(.*?)\}\}")

    def __init__(self, config=None, section=None, parent=None):
        d = super(ConfigSection, self)
        d.__init__()
        self.parent = parent  # used for substitutions
        self.section = section
        if config:            
            for opt in config.options(section):
                value = config.get(section, opt)
                d.__setitem__(opt, value)

    def __getitem__(self, key):
        return self.lookup(key)

    def lookup(self, key, default=None):
        """
        Look up a single key, doing any substitutions as described in the
        module-level docstring.
        """
        value = None
        if self.section:
            try:
                value = os.environ["CONFIG__%s__%s" % (self.section, key)]
            except KeyError:
                pass
        if value == None:
            d = super(ConfigSection, self)
            try:
                value = d.__getitem__(key)
            except KeyError:
                pass

        if value != None:
            return self.mapValue(value)
        else:
            return default
        

    def mapValue(self, value):
        """
        map a string value from the config file to something that has 
        potentially different type and also has the special tokens 
        substituted
        """
        if not isinstance(value, str):
            return value
        
        try:
            return int(value)
        except ValueError:
            pass
        
        try:
            return float(value)
        except ValueError:
            pass
        
        upper = value.upper()
        if upper == "TRUE": return True
        if upper == "FALSE": return False
        if value == "None": return None

        value = self.doSubs(value, self.parent)
        
        return value


    def getVarSub(self, config, section, key):
        """
        get substitution text that will be used to replace a 
        {{var:[section]key}} token - i.e. the variable referred to 
        or else the empty string
        """
        if config:
            try:
                return config[section][key]
            except KeyError:
                pass
        return ""


    def doSub(self, str_, matchobj, sub):
        """
        Given a string, a re.match object and a substitution value,
        return the result of substituting it.  
        
        The substitution value should normally be a string, but in the
        case where the match constitutes the whole string, then just the 
        substitution value itself, so it can then be another data type.
        """
        string1 = str_[ : matchobj.start()]
        string2 = str_[matchobj.end() : ]

        if (not string1) and (not string2):
            return sub

        return string1 + sub + string2


    def doSubs(self, str_, config):
        """
        Given a string and a config object, return a revised value after
        expanding all special tokens (i.e. if none are found then just get 
        the original string back)
        """
        while True:
            m = self._varSubsRe.search(str_)
            if not m:
                break
            section = m.group(1)
            key = m.group(2)
            sub = self.getVarSub(config, section, key)
            str_ = self.doSub(str_, m, sub)

        while isinstance(str_, str):
            m = self._evalSubsRe.search(str_)
            if not m:
                break
            code = m.group(1)
            try:
                sub = eval(code)
            except:
                sub = ""
            str_ = self.doSub(str_, m, sub)
            
        return str_


class BaseConfig(dict):
    """
    See module-level doc for details.

    Note not "AbstractConfig" - this can meaningfully be instantiated, 
    although in fact GlobalConfig and DatasetConfig do subclass it to add
    extra functionality.
    """

    compulsoryVars = []

    def __init__(self, config_file_path, missing_ok = False):
        """
        Instantiate based on given path to config file
        """
        self.d = super(BaseConfig, self)
        self.d.__init__()
        self.config_file_path = config_file_path
        self.missing_ok = missing_ok
        self.settings = []
        self.reread()

    def __getitem__(self, key):
        """
        Return a ConfigSection object based on the specified section of
        the file (or an empty ConfigSection if none)
        """
        if not self.d.has_key(key):
            self.d.__setitem__(key, ConfigSection())  # create an empty section
        return self.d.__getitem__(key)

    def _readConfig(self, config):
        retval = config.read(self.config_file_path)
        if not retval and not self.missing_ok:
            raise RuntimeError("Could not read config file %s" % self.config_file_path)        
    
    def reread(self):
        """
        Unconditionally reread the config file. Returns nothing if file disappeared.
        """
        if not os.path.exists(self.config_file_path):
            return

        self.clear()
        config = ConfigParser.ConfigParser()
        
        self._readConfig(config)

        for section in config.sections():
            self.d.__setitem__(section, ConfigSection(config, section, parent=self))

        # go through the default settings and update the config with the
        # defaults if none have been set so far
        for s in self.settings:
            if not self.checkSet(s[0] + "." + s[1]):
                if not config.has_section(s[0]):
                  config.add_section(s[0])
                  self.d.__setitem__(s[0], ConfigSection(config, s[0], parent=self))
                self.set(s[0] + "." + s[1], s[2])

        self.time_last_read = time.time()
        self.checkCompulsoryVars()


    def readDefaults(self):
        '''
        Read global default values from python settings.py file
        '''
        self.settings = []
        defaults = dir(settings)
        for default in defaults:
            if not default.startswith("__"):
                c = getattr(settings, default)
                d = default.split("_")
                for k in c:
                    e = d[0]
                    self.settings.append((e, k, c[k]))


    def checkCompulsoryVars(self):
        """
        Raise an exception if any compulsory variable does not exist or
        has wrong type. Note that there are no compulsory variables except
        where a subclass (e.g. GlobalConfig / DatasetConfig) defines some.
        """
        for sect, varnames in self.compulsoryVars:
            s = self[sect]
            for v in varnames:
                if isinstance(v, str):
                    varname, vartype = v, None
                else:
                    varname, vartype = v
                if varname not in s:
                    raise Exception("Compulsory variable %s::%s not in %s" %
                                    (sect, varname, self.config_file_path))
                value = s[varname]
                type_ = type(value)
                if vartype and not isinstance(value, vartype):
                    raise Exception("Compulsory variable %s::%s in %s has type %s (value %s), should be %s" %
                                    (sect, varname, self.config_file_path, type_, value, vartype))
                    
        
    def rereadIfUpdated(self):
        """
        Re-reads the config file, if necessary.
        Return value is whether it actually reread or not
        """
        # note: duplicates a test in FileUtils but prefer not to depend on that module here
        if not os.path.exists(self.config_file_path):
            # config has been deleted, maybe intentionally, so don't reread
            return False

        mtime = os.path.getmtime(self.config_file_path)
        if mtime + 1 > self.time_last_read:
            self.reread()
            return True
        else:
            return False

    # set a value for a key
    def set(self, key, value):
        try:
            sk = key.split(".")
            a = self.d.__getitem__(sk[0])
            #b = a[sk[1]]
            a[sk[1]] = value
            self.d.__setitem__(sk[0], a);
        except Exception, ex:
            print str(ex)

    # get the value for a key
    def get(self, key):
        b = None
        try:
            sk = key.split(".")
            a = self.d.__getitem__(sk[0])
            b = a[sk[1]]
        except Exception, ex:
            print str(ex)
        return b

    # check if a key is set and it has
    # somesort of value
    def checkSet(self, key):
        try:
            a = self.get(key)
            if a:
                return True
            return False
        except:
            return False

    # if a keys is set (with the appropriate value),
    # then ensure the other
    # relavent keys are set
    def checkSetIf(self, key, val, keys):
        rv = []
        if self.checkSet(key) == True and self.get(key) != val:
            for k in keys:
                if self.checkSet(k) == False:
                    rv.append(k)
            if len(rv) == 0:
                return None
            return rv
        return None

    def dump(self, stream = sys.stdout):
        """
        For debugging.
        """
        stream.write("\n===Config dump===\n")
        stream.write("Filename = %s\n" % self.config_file_path)
        sections = self.keys()
        sections.sort()
        for section in sections:
            s = self[section]
            stream.write("[%s]\n" % section)
            keys = s.keys()
            keys.sort()
            for k in keys:
                stream.write("  %s = %s (%s)\n" % (k, s[k], type(s[k]).__name__))
        stream.write("===End of config dump===\n\n")
            

if __name__ == '__main__':
    for file in ["../conf/dataset_hadgem2_2xco2.ini", "../conf/global.ini"]:
        a = BaseConfig(file)

        # main test - can we dump the config
        a.dump()

        print "these should be None:"
        print a["asdadsasklejklj"]["adsfasdf"]
        for sect in a:
            print a[sect]["asdfasdfasdfad"]

        # test we can put stuff to existing and non-existing section
        print "Put test:"
        sects = [a.keys()[0], "mysect"]
        for s in sects:
            for k in ["username", "mykey"]:
                print s, k, a[s][k], 
                a[s][k] = "foo"
                print a[s][k]

        print "Reread test:"
        # rereading the config file will wipe the value that we wrote, but we are calling
        # rereadIfUpdated(), so it will only happen if the file modification time is updated
        a["rsync"]["cmd"] = "FOO"
        print a["rsync"]["cmd"]
        a.rereadIfUpdated()
        print a["rsync"]["cmd"]
        os.system("touch %s" % file)
        a.rereadIfUpdated()
        print a["rsync"]["cmd"]
