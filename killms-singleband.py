#!/usr/bin/python

#Take a band, use killms to subtract a sky model

import sys
import config
import os.path

die=config.die
report=config.report
warn=config.warn

if len(sys.argv)<2:
    die('Need a filename for config file')

filename=sys.argv[1]
if not(os.path.isfile(filename)):
    die('Config file does not exist')

if len(sys.argv)<3:
    die('Need a sub-band number')

sb=int(sys.argv[2])
sbs='%03i' % sb
band=sb/10
bs='%02i' % band

cfg=config.LocalConfigParser()
cfg.read(filename)

path=cfg.get('paths','processed')
troot=cfg.get('files','target')
skymodel=cfg.get('killms','skymodel')
skymodel=skymodel % bs

print 'Target is',troot,'sub-band number is',sbs,'band is',band
print 'skymodel is',skymodel

os.chdir(path)

run=config.runner(cfg.getoption('control','dryrun',False)).run

calibms=troot+'_SB'+sbs+'_uv.calib.MS'
killms=troot+'_SB'+sbs+'_uv.killms.MS'
concatms=troot+'_B'+bs+'_concat.MS'

report('Copying data')
run('cp -r '+calibms+' '+killms)
report('Apply phase calibration')
run('calibrate-stand-alone -n --parmdb '+concatms+'/instrument '+killms+' ~/lofar/text/bbs-apply-phaseonly')
report('Run killms')
run('/home/tasse/killMS/killMS/killMS.py --ms='+killms+' --SkyModel='+skymodel+' --NCPU=16 --TChunk=2')
