#!/usr/bin/python
# do the cataloguing on final images

import sys
import config
import os.path
import numpy as np
import lofar.bdsm as bdsm
from astropy.io import fits
from multiprocessing import Process

def convolve_all(files,run):
    
    resolution=0
    for f in files:
        hdulist=fits.open(f)
        bmaj=3600.0*hdulist[0].header['BMAJ']
        if bmaj>resolution:
            resolution=bmaj
        hdulist.close()

    resolution*=1.01
    print 'Convolving everything with circular beam of',resolution,'arcsec'
    rstr=str(resolution)+','+str(resolution)

    for f in files:
        outfile=f[:-5]+'_conv.fits'
        if not os.path.exists(outfile):
            print 'Doing',f,'output to',outfile
            run('fits op=xyin in='+f+' out=tmp')
            run('convol map=tmp fwhm='+rstr+' options=final out=tmp_out')
            run('fits op=xyout in=tmp_out out='+outfile)
            run('rm -r tmp tmp_out')
        else:
            print 'Convolved file',outfile,'already exists'

def findrms(filename,region):
    import pyregion
    from radioflux import radioflux

    fitsfile=fits.open(filename)
    rm=radioflux.radiomap(fitsfile)
    bg_ir=pyregion.open(region).as_imagecoord(rm.prhd)
    bg=radioflux.applyregion(rm,bg_ir)
    return bg.rms

def bs(band):
    return '_B%02i' % band

def work(file):
    print 'Making catalogue for',file
    myout=file+'.catalog'
    if not(os.path.exists(myout)):
        img=bdsm.process_image(file,thresh_pix=5,detection_image='adaptive-stack.fits',fix_to_beam=True,rms_box=(55,12), adaptive_rms_box=True, adaptive_thresh=150, rms_box_bright=(80,20),mean_map='zero')
        img.write_catalog(outfile=myout,clobber='True',format='ascii')
    else:
        print 'Catalog file exists'

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

try:
    suffix=cfg.get('catalog','suffix')
except config.NoOptionError:
    suffix='image_img_masked'

# this is the suffix for the masked images, default is the default for
# the imaging step

combine=cfg.getint('catalog','combine')
# how many bands to combine to measure fluxes

doblank=cfg.getoption('catalog','blank',False)
doconvolve=cfg.getoption('catalog','convolve',True)
rmsregion=cfg.get('catalog','rmsreg')

if doblank:
    report('Blanking all maps')
    for band in range(37):
        imagename=troot+bs(band)+'_'+suffix+'.restored.fits'
        cimagename=troot+bs(band)+'_'+suffix+'.restored.corr.fits'

        if not(os.path.isfile(imagename)):
            warn(imagename+' does not exist')
        else:
            run('/home/mjh/lofar/bin/blanker.py --threshold=1e-6 --neighbours=6 '+imagename+' '+cimagename)
else:
    report('Not blanking any maps')

if doconvolve:
    report('Convolving all maps to common resolution')
    files=[]
    for band in range(37):
        imagename=troot+bs(band)+'_'+suffix+'.restored.fits'
        cimagename=troot+bs(band)+'_'+suffix+'.restored.corr.fits'
        if os.path.isfile(imagename) and os.path.isfile(cimagename):
            files.append(imagename)
            files.append(cimagename)

    print files
    convolve_all(files,run)

report('Adaptively stacking images to make detection image')

rms=[]
iname=[]
cname=[]
for band in range(37):
    if doconvolve:
        imagename=troot+bs(band)+'_'+suffix+'.restored_conv.fits'
        cimagename=troot+bs(band)+'_'+suffix+'.restored.corr_conv.fits'
    else:
        imagename=troot+bs(band)+'_'+suffix+'.restored.fits'
        cimagename=troot+bs(band)+'_'+suffix+'.restored.corr.fits'
    if os.path.isfile(imagename):
        rv=findrms(imagename,rmsregion)
        print 'Band',band,'rms is',rv
    else:
        rv=-1000
    rms.append(rv)
    iname.append(imagename)
    cname.append(cimagename)

medrms=np.median(rms)
print 'median rms is',np.median(rms)

i=0
s=0
w=0
included=[]

report('Doing the uncorrected detection image')

for band in range(37):
    if (rms[band]<medrms*2.5 and rms[band]>medrms/2.0):
        included.append(True)
        print 'Including',iname[band]
        fitsfile=fits.open(iname[band])
        image=fitsfile[0].data[0,0]
        fitsfile.close()
        s+=image/(rms[band]**2.0)
        w+=1.0/(rms[band]**2.0)
    else:
        included.append(False)

s/=w
fitsfile=fits.open(iname[0])
fitsfile[0].data[0,0]=s
fitsfile.writeto('adaptive-stack.fits',clobber=True)
fitsfile.close()

report('Doing the corrected stacked image (for fluxes)')

for band in range(37):
    if included[band]:
        print 'Including',cname[band]
        fitsfile=fits.open(cname[band])
        image=fitsfile[0].data[0,0]
        fitsfile.close()
        s+=image/(rms[band]**2.0)

s/=w
fitsfile=fits.open(cname[0])
fitsfile[0].data[0,0]=s
fitsfile.writeto('adaptive-stack-corr.fits',clobber=True)
fitsfile.close()

# Now start making the catalogues

for band in range(37):
    if included[band]:
        f=troot+bs(band)+'_'+suffix+'.restored.corr_conv.fits'
        work(f)

# Make the master catalogue

work('adaptive-stack-corr.fits')
