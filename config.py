#!/usr/bin/python

import os
import ConfigParser

class LocalConfigParser (ConfigParser.SafeConfigParser):

    """
    Subclass to add a getoption method that takes a default and
    returns it if the section or keyword does not exist
    """

    def getoption(self,section,keyword,default):
        try:
            result=self.getboolean(section,keyword)
            return result
        except ConfigParser.NoOptionError:
            return default

NoOptionError=ConfigParser.NoOptionError
NoSectionError=ConfigParser.NoSectionError

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def die(s):
    print bcolors.FAIL+s+bcolors.ENDC
    raise Exception(s)

def report(s):
    print bcolors.OKGREEN+s+bcolors.ENDC

def warn(s):
    print bcolors.OKBLUE+s+bcolors.ENDC

class runner:
    def __init__(self,dryrun):
        self.dryrun=dryrun
    def run(self,s,proceed=False):
        print s
        if not(self.dryrun):
            retval=os.system(s)
            if not(proceed) and retval!=0:
                die('FAILED to run '+s+': return value is '+str(retval))
            return retval

def getcpus():
    nodefile=os.getenv('PBS_NODEFILE')
    if nodefile:
        lines=len(open(nodefile).readlines())
        return lines
    else:
        import multiprocessing
        return multiprocessing.cpu_count()
