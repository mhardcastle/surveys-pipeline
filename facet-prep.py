#!/usr/bin/python

# Code to prepare 10-sb data that have been through the initial
# calibration phase for facet calibration

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
os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run
bs='%02i' % band
ms=troot+'_B'+bs+'_concat.MS'

if not(os.path.isdir(ms)):
    warn('Concatenated file does not exist! calling makeband...')
    run('/home/mjh/lofar/surveys-pipeline/makeband.py '+filename+' '+str(band))

facetprefix=cfg.get('facet','prefix')
facetsuffix=cfg.get('facet','suffix')
it_template=cfg.get('facet','template')
avems=facetprefix+'_SB'+bs+'0-'+bs+'9.ave.ms'
finalms=facetprefix+'_SB'+bs+'0-'+bs+'9.'+facetsuffix+'.ms'

report('Preparing %s for facet calibration (%s, %s)' % (ms,avems,finalms))

ave_exists=os.path.isdir(avems)
if ave_exists:
    warn('Average ms already exists, not re-making it')

else:
    report('Averaging')
    ndpppname=ms.replace('MS','NDPPP')
    outfile=open(ndpppname,'w')
    outfile.write('msin=['+ms+']\nmsin.datacolumn = DATA\nmsin.baseline = [CR]S*\nmsout='+avems+'\nmsout.datacolumn = DATA\nsteps = [count,avg]\navg.type = average\navg.freqstep = 2\navg.timestep = 2\n')
    outfile.close()
    run('NDPPP '+ndpppname)

    report('Run RFICONSOLE again')
    run('rficonsole -j 8 '+avems)

report('Phase-only calibration')
clusteredmodel=troot+'_B'+bs+'_skymodel_clustered.txt'

if os.path.isfile(clusteredmodel):
    warn('Skymodel already exists, not making it')
else:
    
    freq=getfreq(ms)
    skymodel=cfg.get('skymodel','file')
    if not(os.path.isfile(skymodel)):
        die('Skymodel file '+skymodel+' does not exist!')
    report('Generating sky model for file '+ms+' at frequency '+str(freq)+' Hz')
    outmodel=troot+'_B'+bs+'_skymodel.txt'
    clusteredmodel=troot+'_B'+bs+'_skymodel_clustered.txt'
    
    run('/home/mjh/lofar/bin/first-crossmatch-skymodel.py '+skymodel+' '+outmodel+' '+str(freq))

    report('Clustering the sky model')
    run('/home/mjh/lofar/bin/cluster-first-skymodel.py '+outmodel+' '+clusteredmodel)

if not(os.path.isdir(it_template)):
    report('Making instrument template')
    run('calibrate-stand-alone --numthreads 8 -f '+avems+' /home/mjh/git/facet-calibration/ap_bbstemplate.parset '+clusteredmodel)
    run('mv '+avems+'/instrument '+it_template)


if not(ave_exists):

    report('Doing the phase calibration')
    run('calibrate-stand-alone --numthreads 8 -f '+avems+' /home/mjh/lofar/text/bbs-phaseonly-first-nocorrect '+clusteredmodel)

    report('Applying the beam')
    run('applybeam.py '+avems)

report('Copy corrected data to new dataset')
run('ctod.py '+avems+' '+finalms)

report('Copy instrument table')

run('/home/mjh/git/facet-calibration/parmdbcopy_phaseonlyparmdb_to_ap.py '+finalms+' '+avems+'/instrument '+it_template+' '+finalms+'/instrument_ap_smoothed')

report('Apply calibration')

run('calibrate-stand-alone -v --parmdb-name instrument_ap_smoothed --numthreads 8 '+finalms+' /home/mjh/lofar/text/wendy-apply.txt')
