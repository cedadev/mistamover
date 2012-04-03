# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
add call to set the process name - if we have ctypes available
"""

try:
    import ctypes as C

    def setProcName(name):
        """
        Set the name of the process to be the specified string
        when we do a "ps".

        To avoid big complications, the string will be truncated if it 
        exceeds the length of the existing process name.
        """

        argc_t = C.c_int
        argv_t = C.POINTER(C.c_char_p)  # char**

        argc = argc_t()
        argv = argv_t()

        # get argv array pointer
        func = C.pythonapi.Py_GetArgcArgv
        func.argtypes = [C.POINTER(argc_t),
                         C.POINTER(argv_t)]
        func.restype = None
        func(C.byref(argc), C.byref(argv))

        # in fact Linux will store the args all in sequence, so for most
        # purposes we can get away with setting argv[0] to one long string,
        # but not exceeding the original total length to avoid overwriting the
        # environment which follows it in memory

        maxlen = 0
        for i in range(argc.value):
            maxlen += len(argv[i]) + 1

        C.memset(argv.contents, 0, maxlen)  # nulls

        C.memmove(argv.contents,
                  name,
                  min(len(name), maxlen - 1))

except ImportError:
    def setProcName(name):
        pass
