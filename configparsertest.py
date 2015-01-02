#!/usr/bin/python

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
        except:
            return default

#config = ConfigParser.SafeConfigParser()
config=LocalConfigParser()
config.read('config.cfg')

unpackpath=config.get('paths','unpack')
processedpath=config.get('paths','processed')

croot=config.get('files','calibrator')
troot=config.get('files','target')

print unpackpath,croot

print config.getoption('calibration','antennafix',False)
print config.getoption('calibration','rficonsole',True)
print config.getoption('calibration','smartdemix',False)
