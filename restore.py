#!/usr/bin/python

# restore the model which has been subtracted with killms. 

from astropy.io import fits
from astropy.wcs import WCS
import sys
import numpy as np
import numexpr as ne
import os.path
import config

def gaussian(xsize,ysize,x0,y0,sx,sy,pa):
    X, Y = np.meshgrid(np.arange(0,xsize,1.0), np.arange(0,ysize,1.0))
    pa*=np.pi/180.0
    a=0.5*((np.cos(pa)/sx)**2.0+(np.sin(pa)/sy)**2.0)
    b=0.25*((-np.sin(2*pa)/sx**2.0)+(np.sin(2*pa)/sy**2.0))
    c=0.5*((np.sin(pa)/sx)**2.0+(np.cos(pa)/sy)**2.0)
    
    return ne.evaluate('exp(-(a*(X-x0)**2.0+2*b*(X-x0)*(Y-y0)+c*(Y-y0)**2.0))')

gfactor=2.0*np.sqrt(2.0*np.log(2.0))

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
bs='%02i' % band
cfg=config.LocalConfigParser()
cfg.read(filename)
dryrun=cfg.getoption('control','dryrun',False)
run=config.runner(dryrun).run

path=cfg.get('paths','processed')
troot=cfg.get('files','target')
sky_suffix=cfg.get('imaging','suffix')
suffix=cfg.get('subtracted_image','suffix')

print 'Target is',troot,'band is',band

os.chdir(path)

skymodelname=troot+'_B'+bs+'_'+sky_suffix+'_img.restored.fits.skymodel.filtered.npy'

if not(os.path.isfile(skymodelname)):
    die('Sky model '+skymodelname+' does not exist')

# now work out the names of the fits files from the subtract_image step

imgname=troot+'_B'+bs+'_'+suffix+'_img.restored'

fitsfile=sys.argv[1]

m=np.load(skymodelname)

# blank first
report('Blanking')
run('blanker.py '+imgname+'.fits '+imgname+'.corr.fits')

hdu=fits.open(imgname+'.fits')
rhdu=fits.open(imgname+'.corr.fits')

f=hdu[0].data[0,0]
rf=rhdu[0].data[0,0]
ratio=rf/f
prhd=hdu[0].header
bmaj=prhd.get('BMAJ')
bmin=prhd.get('BMIN')
bpa=prhd.get('BPA')
w=WCS(hdu[0].header)
cd1=-w.wcs.cdelt[0]
cd2=w.wcs.cdelt[1]
if (cd1!=cd2):
    raise Exception('Pixels are not square')
(maxx,maxy)=f.shape
print 'File',fitsfile
print 'BMAJ',bmaj,'BMIN',bmin,'BPA',bpa
print 'Pixel size',cd1
print 'maxx',maxx,'maxy',maxy
bmaj/=cd1
bmin/=cd2
bmaj/=gfactor
bmin/=gfactor
#bpa+=90.0
print 'Gaussian axes in pixels',bmaj,bmin

# do the actual restoring

report('Restoring '+str(len(m))+' Gaussians')

for c in m:
    flux=c[3]
    ra=c[1]*180.0/np.pi
    dec=c[2]*180.0/np.pi
    imc=w.wcs_world2pix([(ra,dec,0,0)],0)
    x=imc[0][0]
    y=imc[0][1]
    print ra,dec,flux,x,y
    if x<0 or y<0 or x>=maxx or y>=maxy:
        print '... skipping, off image'
    elif np.isnan(f[int(y),int(x)]):
        print '... skipping, image blanked at this location'
    else:
        g=gaussian(maxx,maxy,x,y,bmin,bmaj,bpa)
        f+=flux*g
        rf+=ratio*flux*g
    
hdu.writeto(imgname+'.sr.fits',clobber=True)
rhdu.writeto(imgname+'.corr.sr.fits',clobber=True)
