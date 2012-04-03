# BSD Licence
# Copyright (c) 2012, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

class ResponseCode(object):
    """
    We only allow Response codes to be instances of ResponseCode

    The calling code must set them e.g. with
            status = Response.failure

    and can expect at a minimum that status.__nonzero__() will return
    True for success or False for failure.  The implementation 
    can be changed later if a range of failure codes are added

    Codes are also callable - they return Response objects with that code
    and the message (or with 'Success' or 'Failure' if no message given)
    """
    def __init__(self, succeed):
        self.succeed = succeed
    
    def __nonzero__(self):
        return self.succeed

    def __str__(self):
        if self:
            return "Success"
        else:
            return "Failure"

    def __call__(self, msg = None, *args, **kwargs):
        if msg == None:
            msg = str(self)
        return Response(self, msg, *args, **kwargs)

failure = ResponseCode(False)
success = ResponseCode(True)

def successIf(condition, *args, **kwargs):
    """
    return a success or failure Response object depending on condition
    """
    if condition:
        return success(*args, **kwargs)
    else:
        return failure(*args, **kwargs)


class Response(object):

    """
    A response object containing a code (which must be a ResponseCode object)
    and a message, and optionally some additional data.

    Has a __nonzero__() method that is based on success/failure status:
       if response:
          ... stuff to do if it succeeded ...

    also you can add responses, and you will get a useful combination of
    two responses - see doc string for __add__()

    """

    def __init__(self, code, msg, data=None):
        self.code = code
        self.msg = msg
        self.data = data
        if not isinstance(code, ResponseCode):
            raise ValueError("code %s is not a valid response code")
    
    def __str__(self):
        if self.data:
            return "<%s, '%s' (data=%s)>" % (self.code, self.msg, self.data)
        else:
            return "<%s, '%s'>" % (self.code, self.msg)
    
    def __nonzero__(self):
        return self.code.__nonzero__()

    def dup(self):
        """
        can be changed to return self (for performance) if this object is not modifiable???
        """
        return Response(self.code, self.msg)

    def __add__(self, other):
        """
        We can combine our response code with another response code.
        Status is failure if either fails.
        Code is concatenation of any failure messages, or self.code if both succeed.
        """
        if other:
            return self.dup()
        elif self:
            return other.dup()
        else:
            return Response(self.code, "%s, %s" % (self.msg, other.msg))

    def assert_(self):
        """
        Raise an exception if the response was a failure code
        """
        if not self:
            raise Exception(self.msg)


def wrap(method, *args, **kwargs):
    """
    Wrap a method, and return a response code.  The actual return value
    of the method is returned in the optional extra data; the main 
    success/failure code depends on whether there was an exception.
    """
    try:
        return success(data = method(*args, **kwargs))
    except Exception, err:
        return failure("%s: %s" % (Exception, err))
    

class Wrapper(object):
    """
    This turns a generic callable which may raise an exception into
    a callable which will return a Response object depending whether
    an exception was raised or not.

    If it succeeds, then the message is the return value (unless None,
    in which case the default message).
    """
    def __init__(self, method):
        self.method = method

    def __call__(self, *args, **kwargs):
        return wrap(self.method, *args, **kwargs)

    
if __name__ == '__main__':
    fail1 = Response(failure, "angst1")
    fail2 = failure("angst2")
    succ1 = Response(success, "happiness1")
    succ2 = success("happiness2")

    print success, failure, success(), failure()

    print fail1, fail2, succ1, succ2
    if fail1:
        print "should not get here"
    if succ1:
        print "should get here"

    print fail1 + fail2
    print fail1 + succ2
    print succ1 + fail2
    print succ1 + succ2
    
