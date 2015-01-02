#!/usr/bin/python

# make a catalogue for a single band image. 

import sys
import os.path
import config

die=config.die
report=config.report
warn=config.warn

if len(sys.argv)<2:
    die('Need a filename for config file')

filename=sys.argv[1]
if not(os.path.isfile(filename)):
    die('Config file does not exist')

if len(sys.argv)<3:
    die('Need a band number')

band=int(sys.argv[2])
bs='%02i' % band
cfg=config.LocalConfigParser()
cfg.read(filename)
dryrun=cfg.getoption('control','dryrun',False)
run=config.runner(dryrun).run

path=cfg.get('paths','processed')
troot=cfg.get('files','target')
suffix=cfg.get('imaging','suffix')
tchunk=cfg.get('subtraction','tchunk')
ncpu=cfg.get('subtraction','ncpu')
print 'Target is',troot,'band is',band

os.chdir(path)

skymodelname=troot+'_B'+bs+'_'+suffix+'_img.restored.fits.skymodel.filtered.npy'

if not(os.path.isfile(skymodelname)):
    die('Sky model '+skymodelname+' does not exist')

# take a copy to work on
orig=troot+'_B'+bs+'_concat.MS'
if not(os.path.isdir(orig)):
    die('Cannot find original MS '+orig)
copy=troot+'_B'+bs+'_killMS.MS'
report('Copying data to '+copy)
if os.path.isdir(copy):
    warn('Copy already exists, not overwriting it!')
else:
    run('cp -r '+orig+' '+copy)

report('Run killms')
run('/home/tasse/killMS/CohJones/CohJones.py --DoBar=0 --ms='+copy+' --SkyModel='+skymodelname+' --NCPU='+ncpu+' --TChunk='+tchunk)
