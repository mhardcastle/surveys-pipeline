#!/usr/bin/python

import sys
import os,os.path
import config
die=config.die
report=config.report
warn=config.warn

if len(sys.argv)<2:
    die('Need a filename for config file')

filename=sys.argv[1]
if not(os.path.isfile(filename)):
    die('Config file does not exist')

cfg=config.LocalConfigParser()
cfg.read(filename)

troot=cfg.get('files','target')
processedpath=cfg.get('paths','processed')

os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run

sb=0
while sb<366:
    sbs='%03i' % sb
    dir=troot+'_SB'+sbs+'_uv.filter.MS'
    if os.path.isdir(dir):
        break
    sb+=1
else:
    die("Can't find any target files!")

run('calibrate-stand-alone --replace-parmdb '+dir+' /home/mjh/lofar/text/make-template-bbs.txt ~/lofar/text/sources-calibrate.txt')
run('mv '+dir+'/instrument instrument_template_caltransfer')
