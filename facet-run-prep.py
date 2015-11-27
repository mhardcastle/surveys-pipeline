#!/usr/bin/python

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

cfg=config.LocalConfigParser()
cfg.read(filename)

troot=cfg.get('files','target')
processedpath=cfg.get('paths','processed')
os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run

facetprefix=cfg.get('facet','prefix')
facetsuffix=cfg.get('facet','suffix')
facetstart=cfg.getint('facet','start')
facetend=cfg.getint('facet','end')
facetstep=cfg.getint('facet','step')
facetrundir=cfg.get('facet','rundir')
docopy=True
try:
    copyfrom=cfg.get('facet','copyfrom')
except config.NoOptionError:
    docopy=False
    
for i in range(facetstart,facetend+1,facetstep):
    print 'Doing',i,'..',i+facetstep-1
    bs='%02i%02i' % ( i,i+facetstep-1 )
    cdir=facetrundir+bs
    if docopy and cdir==copyfrom:
        warn('Will not update the template directory!')
        continue
    # cdir contains the run directory
    if not(os.path.isdir(cdir)):
        run('mkdir '+cdir)
    for ms in range(i,i+facetstep):
        mss='%02i' % ms
        # rsync the ms
        msname=facetprefix+'_SB'+mss+'0-'+mss+'9.'+facetsuffix+'.ms'
        if os.path.isdir(msname):
            run('rsync -av --delete '+msname+' '+cdir)
            skymodelname=facetprefix+'_SB'+mss+'0-'+mss+'9.skymodel'
            run('cp '+skymodelname+' '+cdir)
        else:
            warn('MS '+str(ms)+' does not exist')
    if docopy:
        report('Copying reference files')
        run('cp '+copyfrom+'/*.rgn '+cdir)
        run('cp '+processedpath+'/facets.txt '+cdir)
        run('cp '+copyfrom+'/parset.py '+cdir)
        run('cp -r '+copyfrom+'/instrument_template_Gain_TEC_CSphase '+cdir)
        run('cd '+cdir+' ; ls -d '+copyfrom+'/*masktmp | awk \'{print "ln -s",$1}\' | sh',proceed=True)

