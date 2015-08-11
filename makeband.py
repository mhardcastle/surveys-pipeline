#!/usr/bin/python

import sys
import config
import os.path
import pyrap.tables as pt

def ctod(infile,outfile):
    print 'copy',infile,'CORRECTED_DATA to',outfile,'DATA'

    pt.tablecopy(infile,outfile,deep=True)

    out_t=pt.table(outfile,readonly=False)
    out_t.removecols('DATA')
    out_t.removecols('MODEL_DATA')
    out_t.removecols('IMAGING_WEIGHT')
    out_t.renamecol('CORRECTED_DATA','DATA')
    out_t.done()

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

# Now make the bands in the specified range and prepare for imaging

for band in range(bb,be+1):
    print 'Band',band
    bs='%02i' % band
    report('Copying corrected data to data')
    sbst=band*10
    sbend=sbst+10
    if sbend>366:
        sbend=366
    flist=''
    for sb in range(sbst,sbend):
        print 'Sub-band',sb
        sbs='%03i' % sb
        infile=troot+'_SB'+sbs+'_uv.filter.MS'
        outfile=troot+'_SB'+sbs+'_uv.calib.MS'
        if os.path.isdir(infile):
            ctod(infile,outfile)
            flist+='"'+outfile+'",'
        else:
            flist+='"",'
    report('Concatenating band')
    outfile=troot+'_B'+bs+'_concat.MS'
    file=open('NDPPP-concat.in','w')
    file.write('msin=['+flist[:-1]+']\nmsin.datacolumn = DATA\nmsout = '+outfile+'\nsteps = []\nmsin.orderms = False\nmsin.missingdata = True\n')
    file.close()
    run('NDPPP NDPPP-concat.in')
