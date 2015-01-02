#!/usr/bin/python

# make a catalogue for a single band image. This is currently
# standalone but if it works will be incorporated into the killms part
# of the pipeline.

import sys
import os.path
import lofar.bdsm as bdsm
import config
from astropy.io import fits

die=config.die
report=config.report
warn=config.warn

def docat(infile):
    print 'Making catalogue for',infile
    txtout=infile+'.catalog'
    smout=infile+'.skymodel'
    if os.path.isfile(smout):
        print 'Catalogue already exists!'
    else:
        img=bdsm.process_image(infile,thresh_pix=5,fix_to_beam=True,rms_box=(55,12), adaptive_rms_box=True, adaptive_thresh=150, rms_box_bright=(80,20),mean_map='zero')
        img.write_catalog(outfile=txtout,clobber='True',format='ascii')
        img.write_catalog(outfile=smout,clobber='True',format='bbs',catalog_type='gaul')
                      
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
flux=float(cfg.get('subtraction','flux'))
frequency=float(cfg.get('subtraction','frequency'))
alpha=float(cfg.get('subtraction','alpha'))
clusters=int(cfg.get('subtraction','clusters'))

print 'Target is',troot,'band is',band

os.chdir(path)

filename=troot+'_B'+bs+'_'+suffix+'_img'

if not(os.path.isfile(filename+'.restored.fits')):
    run('tofits.py '+filename+'.restored')
if not(os.path.isfile(filename+'.restored.corr.fits')):
    run('tofits.py '+filename+'.restored.corr')
run('blanker.py '+filename+'.restored.fits '+filename+'.restored.corr.fits')
    
fitsfile=fits.open(filename+'.restored.fits')
ffreq=fitsfile[0].header['restfrq']
flux*=(ffreq/frequency)**(-alpha)
print 'Flux to cut model at is',flux,'Jy'
fitsfile.close()

if not(dryrun):
    docat(filename+'.restored.fits')

catfile=filename+'.restored.fits.skymodel'
outname=catfile+'.filtered'

if not(dryrun):
    infile=open(catfile)
    outfile=open(outname,'w')

    for l in infile.readlines():
        if 'format' in l:
            outfile.write(l+'\n')
        else:
            bits=l.split(', ')
            if len(bits)>10 and float(bits[4])>=flux:
                outfile.write(l)

    outfile.close()
    infile.close()

run('/home/tasse/killMS/CohJones/MakeModel.py --SkyModel='+outname+' --NCluster=30 --DoPlot=0 --CMethod=2')
