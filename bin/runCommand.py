#!/usr/bin/python
# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# this module provides runCommand.runCommand, which is similar to 
# command.getstatusoutput, except this one invokes the command without
# a shell, instead of using os.popen() which uses a shell
#
# Alan Iwi is to blame for this module
#
import os
import sys
import select
import fcntl


def runCommand(cmd, input=""):
    """
    runCommand(cmd) -> status,output,error

    returns status, output of executing cmd directly without a shell.

    Inputs:

      cmd is a list/tuple containing command and arguments
      (or cmd can be a string, but in that case the command takes no arguments)

      input is a string

    status is an integer
    output is a string
    
    """

    pread,cwrite = os.pipe()
    preaderr,cwriteerr = os.pipe()
    cread,pwrite = os.pipe()
    
    pid=os.fork()
    if (pid==0):
        # child
        os.close(pread)
        os.close(preaderr)
        os.close(pwrite)
        os.dup2(cread,0)
        os.dup2(cwrite,1) #stdout
        os.dup2(cwriteerr,2) #stderr

        if type(cmd)==str:
            command,args = cmd,(cmd,)
        else:
            command,args = cmd[0],cmd

        try:
            os.execvp(command,args)
        except os.error, (errno, message):
            os.write(2,"exec: %s: %s\n" % (command,message))
            os.close(1)
            os.close(2)
            os._exit(1)

    # parent
    os.close(cwrite)
    os.close(cwriteerr)
    os.close(cread)

    nonblocking(pwrite)

    output=""
    error=""

    rlist=[pread,preaderr]
    wlist=[pwrite]

    chunksize=2048
    
    while 1:
        r,w,x = select.select(rlist,wlist,[])

        if r:
            for fd in r:
                dataread = os.read(fd,chunksize)
                if dataread.__len__() == 0:
                    os.close(fd)
                    rlist.remove(fd)
                else:
                    if fd == pread:
                        output += dataread
                    elif fd == preaderr:
                        error += dataread

        if w:
            if input.__len__() != 0:
                charswritten = os.write(pwrite,input)
                input=input[charswritten:]
            else:
                os.close(pwrite)
                wlist=[]

        if not wlist and not rlist:
            break

    pid,status = os.waitpid(pid,0)
    return status/256, output, error


def nonblocking(fd):
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, os.O_NONBLOCK | flags)


#-------------------------------------------------------------
# Test cases follow.

if __name__ == "__main__":

    def show(string,max=500):
        len=string.__len__()
        if len > max:
            return "(%d bytes)" % len
        else:
            return string

    def runCommand_wrap(cmd, input=""):
        print 'Command: ',cmd

        print 'STDIN: '
        print show(input)
        (status,output,error) = runCommand(cmd,input)
        print 'Status: ',status

        print 'STDOUT: '
        print show(output)
        print 'STDERR: '
        print show(error)
        print "=========="
        return status,output,error
    

    # this command should succeed
    runCommand_wrap(('rev'),'20\n14\n123')

    # this command should also succeed, and has a command-line option
    runCommand_wrap(('sort','-n'),'20\n14\n123')

    # this command should succeed with no output
    runCommand_wrap(('true'))

    # this command should succeed, and has no input
    runCommand_wrap(('head','/etc/passwd'))

    # this command should exec but then return an error
    runCommand_wrap(('cat','/etc/asdfasdfasdfasdf'))

    # this command should fail to exec
    runCommand_wrap(('asdjklasdfjklasdf'))

    s=''
    for i in range(0,100000):
        s+='a'
    # this command will read/write a lot of data - need to do so in alternating
    # chunks.
    (status,output,error) = runCommand_wrap('cat',s)
    
