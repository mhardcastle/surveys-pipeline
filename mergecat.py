#!/usr/bin/python
# code to merge the catalogues using the adaptive-stack catalogue as a guide

from astropy.table import Table
import os.path
import numpy as np

print 'reading master catalogue'

master = Table.read('adaptive-stack-corr.fits.catalog', format='ascii.commented_header', header_start=-1)
master.sort('Total_flux')
master.reverse()

tlist=[]
flist=[]
clist=[]
for i in range(37):
    print 'reading catalogue',i
    catname='L221266_B%02i_image-20_first_img_masked.restored.corr_conv.fits.catalog' % i
    if os.path.isfile(catname):
        f=open(catname)
        for i in range(3):
            line=f.readline()
        bits=line.split()
        freq=bits[8]
        print 'frequency is',freq
        flist.append(freq)
        clist.append('%3i' % (float(freq)/1e6))
        tab=Table.read(f, format='ascii.commented_header', header_start=-1)
        tab['used']=False
        tlist.append(tab)

print clist

# add columns

print 'Adding columns to master table'

master['counterparts']=0
for fr in clist:
    master['s'+fr]=np.nan
    master['e'+fr]=np.nan

# Now go through the master catalogue looking for counterparts

for r in master:
    ra=r['RA']
    dec=r['DEC']
    flux=r['Total_flux']
    print 'Checking for counterpart to Gaussian',r['Gaus_id'],ra,dec,flux
    cs=0
    for m,fr in zip(tlist,clist):
        err=m['E_RA']**2.0+m['E_DEC']**2.0
        dra=m['RA']-ra
        ddec=m['DEC']-dec
        dist2=dra**2.0+ddec**2.0
        dist=np.sqrt(dist2)
        derr=dist/np.sqrt(err)
        dflux=(m['Total_flux']-flux)**2.0
        rayleigh=np.log(dist/err)-dist2/(2*err)-dflux/(2*0.05*m['Total_flux']**2.0)
        rayleigh[m['used']]=-999999
        minindex=np.argmax(rayleigh)
        if rayleigh[minindex]>-2:
#            print rayleigh[minindex],derr[minindex],m['Total_flux'][minindex]
            cs+=1
            r['s'+fr]=m['Total_flux'][minindex]
            r['e'+fr]=m['E_Total_flux'][minindex]
            m['used'][minindex]=True
    print 'Total counterparts',cs
    r['counterparts']=cs
    

master.write('master-table.dat',format='ascii.commented_header')
for i,m in enumerate(tlist):
    print i,len(m),np.sum(m['used'])
