#!/usr/bin/python

import sys
import config
import os.path
import montage_wrapper as montage
import numpy as np
from astropy.io import fits

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
image_suffix=cfg.get('imaging','suffix')
processedpath=cfg.get('paths','processed')
try:
    beampath=cfg.get('imaging','altdir')
except:
    beampath=processedpath
os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run

facetstart=cfg.getint('facet','start')
facetend=cfg.getint('facet','end')
facetstep=cfg.getint('facet','step')
facetrundir=cfg.get('facet','rundir')

for i in range(facetstart,facetend+1,facetstep):
    print 'Doing',i,'..',i+facetstep-1
    bs='%02i%02i' % ( i,i+facetstep-1 )
    cdir=facetrundir+bs
    mosfile=cdir+'/mosaic.fits'
    if not(os.path.isfile(mosfile)):
        die('Can\'t find '+mosfile)
    print 'Mosaic file is',mosfile
    hdrfile=mosfile.replace('.fits','.hdr')
    montage.mGetHdr(mosfile,hdrfile)

    # now loop over the appropriate beam images
    for band in range(i,i+facetstep):
        b1s='%02i' % band
        beamimage=beampath+'/'+troot+'_B'+b1s+'_'+image_suffix+'_img0.avgpb'
        beamfits=beamimage+'.fits'
        if not(os.path.isfile(beamfits)):
            if not(os.path.isdir(beamimage)):
                die('Can\'t find '+beamimage)
            run('tofits.py '+beamimage)
        else:
            print 'FITS version of beam exists, not converting'

        projout=cdir+'/beam-'+b1s+'.fits'
        if not(os.path.isfile(projout)):
            print 'projecting',beamfits,'to',projout
            montage.mProjectPP(beamfits,projout,hdrfile)
        else:
            print 'projected file already exists, not re-making'

        projout32=cdir+'/beamsp-'+b1s+'.fits'
        if not(os.path.isfile(projout32)):
            montage.mConvert(projout,projout32,bitpix=-32)
        else:
            print 'single-precision version exists, not converting'

    os.chdir(cdir)
    if not(os.path.isfile('mosaic-corr.fits')):
        # make a corrected mosaic image from the mean of the beam images
        # take the square root before forming the mean... this seems most
        # likely to be correct!
        f=fits.open('mosaic.fits')
        beam=np.zeros_like(f[0].data)
        for band in range(i,i+facetstep):
            b1s='%02i' % band
            beamfile='beamsp-'+b1s+'.fits'
            bf=fits.open(beamfile)
            beam+=np.sqrt(bf[0].data)
            bf.close()
        beam/=float(facetstep)
        f[0].data/=beam
        f.writeto('mosaic-corr.fits',clobber=True)
        f[0].data=beam
        f.writeto('mosaic-beam.fits',clobber=True)
    else:
        print 'corrected mosaic exists, not re-making'
        
