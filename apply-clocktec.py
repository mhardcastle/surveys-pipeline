#!/usr/bin/python

# Apply the clock-TEC separation from Reinout's method
# This is instead of gain transfer on a per-subband basis as in calib.py

import sys
import config
import os.path
import pyrap.tables as pt

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

band=int(sys.argv[2])

cfg=config.LocalConfigParser()
cfg.read(filename)

troot=cfg.get('files','target')
processedpath=cfg.get('paths','processed')

os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run

sbs='%03i' % band
ms=troot+'_SB'+sbs+'_uv.filter.MS'
if not(os.path.isdir(ms)):
    die('MS does not exist')

globaldbname = 'cal.h5' # input h5 parm file
t = pt.table('globaldb/OBSERVATION', readonly=True, ack=False)
calsource=t[0]['LOFAR_TARGET'][0]

report('Generating clock-tec parmdb')
run('python /home/mjh/lofar/surveys-pipeline/transfer_amplitudes+clock+offset.py '+ms+' '+ms+'/instrument . '+calsource)
report('Applying clock-tec/gain')
run('calibrate-stand-alone '+ms+' /home/mjh/lofar/text/apply-calibration-nb.txt')
