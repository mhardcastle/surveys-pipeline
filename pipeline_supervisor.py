#!/usr/bin/python

#check up on the status of a pipeline run using the config files.

import config
import os
import sys

def bs(band):
    return '_B%02i' % band

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
    imagesuffix=cfg.get('imaging','suffix')
    subimagesuffix=cfg.get('subtracted_image','suffix')
    domask=cfg.getoption('imaging','domask',True)
    if domask:
        add='_img_masked'
    else:
        add='_img'
    os.chdir(processedpath)

    suffixes=['concat.MS',imagesuffix+add+'.restored.fits',imagesuffix+add+'.restored.fits.skymodel.filtered.npy','killMS.MS_killMS.CohJones.sols.npz',subimagesuffix+add+'.restored.fits',subimagesuffix+add+'.restored.sr.fits']
    descriptions=['concatenated data','original FITS image','killMS sky model','killMS solution','subtracted image','restored image']

    for band in range(37):
        for s,t in zip(suffixes,descriptions):
            filename=troot+bs(band)+'_'+s
            if not(os.path.exists(filename)):
                print 'Band',band,t,'does not exist'
                break
        else:
            print 'Band',band,'all OK'

