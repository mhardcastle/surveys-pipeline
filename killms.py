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
    report('Copying file '+orig)

    file=open('NDPPP-temp-'+bs,'w')
    file.write('msin=['+orig+']\nmsin.datacolumn = CORRECTED_DATA\nmsin.baseline = [CR]S*&\nmsout = '+copy+'\nsteps = []\n')
    file.close()

    run('NDPPP NDPPP-temp-'+bs)

report('Add CASA imaging columns')
run('/home/tasse/killMS2/MSTools.py --ms='+copy+' --Operation=CasaCols --TChunk=1')
report('Run killms')
run('/home/mjh/killMS2/killMS.py --ms='+copy+' --SkyModel='+skymodelname+' --NCPU='+ncpu+' --TChunk='+tchunk+' --InCol=DATA --OutCol=CORRECTED_DATA --DoBar=0 --UVMinMax=1,100')
run('mv '+copy+'/killMS.CohJones.sols.npz '+copy+'_killMS.CohJones.sols.npz')

# Remove anything left behind, whether killms lived or not
run('/home/mjh/lofar/surveys-pipeline/tidy-shm.sh')
