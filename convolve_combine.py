#!/usr/bin/python

# convolve and combine the final images

# this is an adaptation of makecat.py: at some point changes made here
# will be fed back into makecat.

import sys
import config
import os.path
import numpy as np
import lofar.bdsm as bdsm
from astropy.io import fits

def convolve_resolution(bmaj1,bmin1,bpa1,bmaj2,bmin2,bpa2):

    '''
    Work out the 'parameters of a Gaussian deconvolved with another
    Gaussian. In other words, the parameters needed to convolve a map
    of a given resolution to another, specified resolution. Here
    bmaj1,bmin1,bpa1 are the desired final resolution -- should be
    floats. bmaj2, bmin2, bpa2 are the resolution of the map(s) of
    interest. Position angles are assumed to be in radians. The
    returned tuple is of the same size as (bmaj2,bmin2,bpa2).

    Unlike the original Fortran code there is no error checking.
    Errors are signalled by the presence of NaNs in the returned
    arrays: use np.isnan to check whether the convolution can be
    performed.
    '''

#import to assist in direct copy of Fortran
    from numpy import sin,cos,arctan2,sqrt

    theta1=bpa1
    theta2=bpa2

    alpha=((bmaj1*cos(theta1))**2 + (bmin1*sin(theta1))**2-
           (bmaj2*cos(theta2))**2 - (bmin2*sin(theta2))**2)
    beta=((bmaj1*sin(theta1))**2 + (bmin1*cos(theta1))**2 -
          (bmaj2*sin(theta2))**2 - (bmin2*cos(theta2))**2)
    gamma  = 2.0*( (bmin1**2-bmaj1**2)*sin(theta1)*cos(theta1) -
                   (bmin2**2-bmaj2**2)*sin(theta2)*cos(theta2) )

    s = alpha + beta
    t = sqrt((alpha-beta)**2 + gamma**2)

    bmaj = sqrt(0.5*(s+t))
    bmin = sqrt(0.5*(s-t))
    bpa = 0.5 * arctan2(-gamma,alpha-beta)

    return bmaj,bmin,bpa

def find_resolution(files):
    bmajl=[]
    bminl=[]
    bpal=[]
    # read in the resolutions of all the files
    for f in files:
        hdulist=fits.open(f)
        bmajl.append(3600.0*hdulist[0].header['BMAJ'])
        bminl.append(3600.0*hdulist[0].header['BMIN'])
        bpal.append(hdulist[0].header['BPA'])
        hdulist.close()

    map_bmaj=np.array(bmajl)
    map_bmin=np.array(bminl)
    map_bpa=np.array(bpal)*np.pi/180.0

    print map_bmaj, map_bmin, map_bpa

    print 'Thinking...'
    gridsteps=100
    minb=np.min(map_bmin)/1.1
    maxb=np.max(map_bmaj)*1.5
    minsize=maxb*maxb*2.0
    bgaxis=np.linspace(minb,maxb,gridsteps)
    bpaxis=np.linspace(-np.pi/2.0,np.pi/2.0,gridsteps)
    for i in range(gridsteps):
        bmaj=bgaxis[i]
        for j in range(0,i+1):
            bmin=bgaxis[j]
            for k in range(gridsteps):
                bpa=bpaxis[k]
                resbmaj,resbmin,resbpa=convolve_resolution(bmaj,bmin,bpa,map_bmaj,map_bmin,map_bpa)
                if np.sum(np.isnan(resbmaj))>0 or np.sum(np.isnan(resbmin))>0 or np.sum(np.isnan(resbpa))>0:
                    continue
    #            print bmaj,bmin,bpa,resbmaj,resbmin,resbpa
#                print '.',
                size=bmaj*bmin
                if size<minsize:
                    minsize=size
                    smallest=(bmaj,bmin,bpa)

    return smallest

def convolve_all(files,resolution,run):
    
    bmaj,bmin,bpa=resolution
    bpa*=180.0/np.pi

    print 'Convolving everything to a resolution of ',resolution
    rstr=str(bmaj)+','+str(bmin)

    for f in files:
        outfile=f[:-5]+'_conv.fits'
        if not os.path.exists(outfile):
            print 'Doing',f,'output to',outfile
            run('fits op=xyin in='+f+' out=tmp')
            run('convol map=tmp fwhm='+rstr+' pa='+str(bpa)+' options=final out=tmp_out')
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

def makecat(file):
    print 'Making catalogue for',file
    myout=file+'.catalog.fits'
    if not(os.path.exists(myout)):
        img=bdsm.process_image(file,thresh_pix=10,thresh_isl=10,detection_image='adaptive-stack-0.fits',rms_map=True,rms_box=(80,20), adaptive_rms_box=True, adaptive_thresh=80, rms_box_bright=(40,10),mean_map='zero')
        img.write_catalog(outfile=myout,clobber='True',format='fits',catalog_type='srl')
    else:
        print 'Catalog file exists'

if __name__=='__main__':

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
    do_makecat=cfg.getoption('combine','makecat',False)
    os.chdir(processedpath)
    run=config.runner(cfg.getoption('control','dryrun',False)).run

    try:
        suffix=cfg.get('combine','suffix')
    except config.NoOptionError:
        suffix='image_img_masked'

    try:
        bandgroups=int(cfg.get('combine','bandgroups'))
    except config.NoOptionError:
        bandgroups=0

    # this is the suffix for the masked images, default is the default for
    # the imaging step

    doblank=cfg.getoption('combine','blank',False)
    doconvolve=cfg.getoption('combine','convolve',True)
    restored=cfg.getoption('combine','restored',False)
    rmsregion=cfg.get('combine','rmsreg')
    if restored:
        rs='.sr'
    else:
        rs=''

    if doblank:
        report('Blanking all maps')
        for band in range(37):
            # check for maps restored after killms
            imagename=troot+bs(band)+'_'+suffix+'.restored'+rs+'.fits'
            cimagename=troot+bs(band)+'_'+suffix+'.restored.corr'+rs+'.fits'

            if not(os.path.isfile(imagename)):
                warn(imagename+' does not exist')
            else:
                run('/home/mjh/lofar/bin/blanker.py --threshold=1e-6 --neighbours=6 '+imagename+' '+cimagename)
    else:
        report('Not blanking any maps')

    if doconvolve:
        files=[]
        cfiles=[]
        for band in range(37):
            imagename=troot+bs(band)+'_'+suffix+'.restored'+rs+'.fits'
            cimagename=troot+bs(band)+'_'+suffix+'.restored.corr'+rs+'.fits'
            if os.path.isfile(imagename) and os.path.isfile(cimagename):
                files.append(imagename)
                cfiles.append(cimagename)

        print files
        report('Finding smallest convolving resolution')
        resolution=find_resolution(files)
        print resolution
        report('Doing the convolution')
        convolve_all(files+cfiles,resolution,run)

    report('Adaptively stacking images to make detection image')

    rms=[]
    iname=[]
    cname=[]
    bands=[]
    for band in range(37):
        if doconvolve:
            imagename=troot+bs(band)+'_'+suffix+'.restored'+rs+'_conv.fits'
            cimagename=troot+bs(band)+'_'+suffix+'.restored.corr'+rs+'_conv.fits'
        else:
            imagename=troot+bs(band)+'_'+suffix+'.restored'+rs+'.fits'
            cimagename=troot+bs(band)+'_'+suffix+'.restored.corr'+rs+'.fits'
        if os.path.isfile(imagename):
            rv=findrms(imagename,rmsregion)
            print 'Band',band,'rms is',rv
            bands.append(band)
        else:
            rv=-1000
        rms.append(rv)
        iname.append(imagename)
        cname.append(cimagename)

    rms=np.array(rms)

    ranges=[bands]
    if bandgroups:
        min=0
        max=bandgroups
        while max<37:
            if max==36:
                max=37
            ranges.append(range(min,max))
            min=max
            max+=bandgroups
# bodge, fix w parameters later
#    ranges.append(range(0,37))

    for i,r in enumerate(ranges):
    
        report('Doing the uncorrected detection image (%i)' % i)
        included=[False]*37
        s=0
        w=0
        medrms=np.median(rms[r])
        print 'median rms is',medrms

        for band in r:
            if (rms[band]<medrms*2.5 and rms[band]>medrms/2.0):
                print 'Including',iname[band]
                fitsfile=fits.open(iname[band])
                image=fitsfile[0].data[0,0]
                fitsfile.close()
                s+=image/(rms[band]**2.0)
                w+=1.0/(rms[band]**2.0)
                included[band]=True

        s/=w

        # use this to make sure that FITS headers at least roughly match
        # frequency range in use
        middle=r[1+len(r)/2]
        while not(included[middle]):
            middle-=1
        fitsfile=fits.open(iname[middle])
        fitsfile[0].data[0,0]=s
        fitsfile.writeto('adaptive-stack-%i.fits' % i,clobber=True)
        fitsfile.close()

        report('Doing the corrected stacked image (for fluxes)')

        for band in r:
            if included[band]:
                print 'Including',cname[band]
                fitsfile=fits.open(cname[band])
                image=fitsfile[0].data[0,0]
                fitsfile.close()
                s+=image/(rms[band]**2.0)

        s/=w
        fitsfile=fits.open(cname[middle])
        fitsfile[0].data[0,0]=s
        fitsfile.writeto('adaptive-stack-corr-%i.fits' % i,clobber=True)
        fitsfile.close()

if do_makecat:
    makecat('adaptive-stack-corr-0.fits')
    for band in range(37):
        if included[band]:
            f=troot+bs(band)+'_'+suffix+'.restored.corr_conv.fits'
            makecat(f)
