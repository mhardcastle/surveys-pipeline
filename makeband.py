#!/usr/bin/python

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
    die('Need a band number')

bb=int(sys.argv[2])

if len(sys.argv)==4:
    be=int(sys.argv[3])
else:
    be=bb

cfg=config.LocalConfigParser()
cfg.read(filename)

troot=cfg.get('files','target')
processedpath=cfg.get('paths','processed')
os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run
try:
    bad_sblist=eval(cfg.get('calibration','badsblist'))
except:
    bad_sblist=[]

# Now make the bands in the specified range

for band in range(bb,be+1):
    print 'Band',band
    bs='%02i' % band
    sbst=band*10
    sbend=sbst+10
    if sbend>366:
        sbend=366
    flist=''
    for sb in range(sbst,sbend):
        sbs='%03i' % sb
        infile=troot+'_SB'+sbs+'_uv.filter.MS'
        if os.path.isdir(infile) and sb not in bad_sblist:
            flist+='"'+infile+'",'
        else:
            flist+='"",'
    report('Concatenating band')
    outfile=troot+'_B'+bs+'_concat.MS'
    filename='NDPPP-concat-'+bs+'.in'
    file=open(filename,'w')
    file.write('msin=['+flist[:-1]+']\nmsin.datacolumn = CORRECTED_DATA\nmsout = '+outfile+'\nsteps = []\nmsin.orderms = False\nmsin.missingdata = True\n')
    file.close()
    run('NDPPP '+filename)
