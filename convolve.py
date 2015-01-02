#!/usr/bin/python

# requires module load miriad

import os
import os.path
import glob
import sys

def convolve(infile,outfile,resolution):

    rstr=str(resolution)+','+str(resolution)
    print 'Doing',infile,'output to',outfile
    os.system('fits op=xyin in='+infile+' out=tmp')
    os.system('convol map=tmp fwhm='+rstr+' options=final out=tmp_out')
    os.system('fits op=xyout in=tmp_out out='+outfile)
    os.system('rm -r tmp tmp_out')

if __name__=='__main__':
    try:
        infile=sys.argv[1]
        outfile=sys.argv[2]
        resolution=float(sys.argv[3])
        convolve(infile,outfile,resolution)
    except IndexError:
        print 'Syntax: convolve.py infile outfile resolution/arcsec'

