#!/usr/bin/python

# Run sagecal on a dataset

import sys
import config
import os.path
import pyrap.tables as pt
from astropy.io import ascii
import calcflux

sources=[['3C286',[27.477,-0.158, 0.032, -0.180]],['3C287',[16.367,-0.364]]]

sagecal_binary='/home/mjh/sagecal-code/src/MS/sagecal'

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

cfg=config.LocalConfigParser()
cfg.read(filename)

troot=cfg.get('files','target')
processedpath=cfg.get('paths','processed')
os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run

sagecalsource=cfg.get('sagecal','source')
sagecalcluster=cfg.get('sagecal','cluster')
sagecalinterval=cfg.getoption('sagecal','interval',default='120')

sb=int(sys.argv[2])
sbs='%03i' % sb

infile=troot+'_SB'+sbs+'_uv.filter.MS'
outfile=troot+'_SB'+sbs+'_uv.sagecal.MS'

# Now modify the source model based on the sub-band frequency

t = pt.table(infile+'/SPECTRAL_WINDOW', readonly=True, ack=False)
freq = t[0]['REF_FREQUENCY']
t.close()

sourcein=ascii.read(sagecalsource)
newsc='lsm-'+sbs+'.txt'
for line in sourcein:
    name=line['col1']
    for (s,c) in sources:
        if s==name:
            flux=calcflux.flux(c,freq)
            print 'Recalculated flux for',s,'is',flux
            line['col8']=flux
ascii.write(sourcein,output=newsc,format='no_header')

file=open('NDPPP-ctod'+sbs+'.in','w')
file.write('msin=['+infile+']\nmsin.datacolumn = CORRECTED_DATA\nmsout = '+outfile+'\nsteps = []\n')
file.close()
run('NDPPP NDPPP-ctod'+sbs+'.in')

run('addImagingColumns.py '+outfile)
run(sagecal_binary+' -d '+outfile+' -s '+newsc+' -c '+sagecalcluster+' -t '+sagecalinterval+' -p solutions'+sbs+'.txt')
