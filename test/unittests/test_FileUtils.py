# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import sys, os

this_dir = os.path.dirname(__file__)
if os.path.basename(this_dir) != "unittests":
    raise Exception("Must be run from 'test' directory to work.")

top_dir = os.path.abspath(os.path.dirname(this_dir))
lib_dir = os.path.join(top_dir, "../lib")
sys.path.append(lib_dir)

import FileUtils

if __name__ == '__main__':
    import commands

    f = FileUtils.FileUtils()

    def test_md5():
        for fname in ["/boot/vmlinuz", "/dev/null", "/etc/passwd"] :
            print "We reckon:               %s  %s" % (f.calcChecksum(fname), fname)
            output = commands.getoutput("md5sum %s" % fname)                        
            print "md5sum command reckons: ", output                                
            print ""                                                                
                                                                                    
    def test_deleteFile():                                                          
        fname = "myfile"                                                            
        os.system("cal > %s" % fname)                                               
        was = os.path.exists(fname)                                                 
        print f.deleteFile(fname)                                                   
        is_now = os.path.exists(fname)                                              
        assert was and not is_now                                                   

    def test_zipDir():
        zipfile = "myfile.zip"
        print f._zipDir("/etc/init.d", "/tmp/myfile.zip")
        print f.zipDir("/etc/init.d", zipfile)           
        os.system("unzip -l %s" % zipfile)                
        os.remove(zipfile)                                

    def test_dirSize():
        print f.getDirSize("/etc/init.d")

    def test_deleteDir():
        tmp_path = "/tmp/my_X11_copy"
        print "copying..."           
        os.system("cp -Rp /etc/X11 %s" % tmp_path)
        os.system("ls -l %s" % tmp_path)              
        dirs = ["%s/xdm" % tmp_path]
        for d in dirs: os.chmod(d, 0)
        print "deleting..."
        print f.deleteDir(tmp_path, stop_on_first_error=False)
        print f.deleteDir(tmp_path)

        for d in dirs: os.chmod(d, 0755)
        print f.deleteDir(tmp_path)

        os.system("ls -l %s" % tmp_path)

    def test_ensureDirExists():
        for i in [1, 2]:
            print f.ensureDirExists("/tmp/this/path/really/exists")

    def test_getMountPointForPath():
        for path in ['/', '/etc', '/home/iwi', '/home/and/another/one',
                     '/tmp/xfers']:
            print path, f.getMountPointForPath(path)

    if len(sys.argv) == 2:
        if sys.argv[1] == "--md5":
            test_md5()
        if sys.argv[1] == "--deleteFile":
            test_deleteFile()
        if sys.argv[1] == "--zipDir":
            test_zipDir()
        if sys.argv[1] == "--dirSize":
            test_dirSize()
        if sys.argv[1] == "--deleteDir":
            test_deleteDir()
        if sys.argv[1] == "--ensureDirExists":
            test_ensureDirExists()
        if sys.argv[1] == "--getMountPointForPath":
            test_getMountPointForPath

