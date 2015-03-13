#!/usr/bin/python

# apply a sky model generated from a FITS file to the output from makeband.

import sys
import config
import os.path
import pyrap.tables as pt

def getfreq(ms):
    t = pt.table(ms+'/SPECTRAL_WINDOW', readonly=True, ack=False)
    freq = t[0]['REF_FREQUENCY']
    t.close()
    return freq

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

cfg=config.LocalConfigParser()
cfg.read(filename)

troot=cfg.get('files','target')
processedpath=cfg.get('paths','processed')
skymodel=cfg.get('skymodel','file')
os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run
beam_applied=cfg.getoption('control','beam_applied',False)

bs='%02i' % band
ms=troot+'_B'+bs+'_concat.MS'

freq=getfreq(ms)

report('Generating sky model for file '+ms+' at frequency '+str(freq)+' Hz')
outmodel=troot+'_B'+bs+'_skymodel.txt'
clusteredmodel=troot+'_B'+bs+'_skymodel_clustered.txt'

run('/home/mjh/lofar/bin/first-crossmatch-skymodel.py '+skymodel+' '+outmodel+' '+str(freq))

report('Clustering the sky model')
run('/home/mjh/lofar/bin/cluster-first-skymodel.py '+outmodel+' '+clusteredmodel)

report('Calibrating with the clustered model')
if beam_applied:
    run('calibrate-stand-alone --numthreads 8 -f '+ms+' /home/mjh/lofar/text/bbs-phaseonly-first-nobeam '+clusteredmodel)
else:
    run('calibrate-stand-alone --numthreads 8 -f '+ms+' /home/mjh/lofar/text/bbs-phaseonly-first '+clusteredmodel)
