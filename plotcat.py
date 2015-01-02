#!/usr/bin/python

# do some plotting using the master catalogue file

from astropy.table import Table
import os.path
import numpy as np
import matplotlib.pyplot as plt

def nanmean(a):
    na=np.array(a)
    return np.mean(na[np.isfinite(na)])

t=Table.read('master-table.dat',format='ascii.commented_header', header_start=-1)
flist=[]
clist=[]
for i in range(37):
    catname='L221266_B%02i_image-20_first_img_masked.restored.corr_conv.fits.catalog' % i
    if os.path.isfile(catname):
        f=open(catname)
        for i in range(3):
            line=f.readline()
        bits=line.split()
        freq=bits[8]
        flist.append(freq)
        clist.append('%3i' % (float(freq)/1e6))

print flist, clist

f=[]
mf=[]
for r in t:
    if r['counterparts']>10:
        v=[]
        for c in clist:
            v.append(r['s'+c])
        plt.plot(flist,v)
        mf.append(nanmean(v))
        f.append(r['Total_flux'])
                  
plt.loglog()
plt.show()

plt.scatter(f,mf)
plt.loglog()
plt.show()
