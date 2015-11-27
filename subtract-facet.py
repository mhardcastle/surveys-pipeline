#!/usr/bin/python

# Do the facet subtraction

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
    die('Need a band number')

band=int(sys.argv[2])

cfg=config.LocalConfigParser()
cfg.read(filename)

troot=cfg.get('files','target')
processedpath=cfg.get('paths','processed')
tempdir=cfg.get('paths','work')
os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run
bs='%02i' % band
ms=troot+'_B'+bs+'_concat.MS'
facetprefix=cfg.get('facet','prefix')
facetsuffix=cfg.get('facet','suffix')
it_template=cfg.get('facet','template')
finalms=facetprefix+'_SB'+bs+'0-'+bs+'9.'+facetsuffix+'.ms'

report('Doing facet calibration subtraction for %s' % (finalms))

report('Writing parset')

parsetname='suball-'+bs+'.py'
outfile=open(parsetname,'w')
outfile.write('SCRIPTPATH=\'/home/mjh/git/facet-calibration\'\nwsclean=\'/home/mjh/wsclean-1.9/build/wsclean\'\nmslist=[\''+finalms+'\']\ncasaregion=\'\'\ncleanup=False\nlogfile=\'subtract-'+bs+'.log\'\ntempdir=\''+tempdir+'\'\n')
outfile.close()

report('Run subtract')

run('python /home/mjh/git/facet-calibration/subtractallcc_wsclean_v2.py '+parsetname)
