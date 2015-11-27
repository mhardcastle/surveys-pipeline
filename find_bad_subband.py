#!/usr/bin/python

import tables
import matplotlib.pyplot as plt
import sys
import os.path
import numpy as np

from losoto.h5parm import h5parm
from losoto.operations_lib import *

try:
    filename=sys.argv[1]
except:
    print 'Need a filename'
    sys.exit(1)

try:
    H = h5parm(filename, readonly=True)
except:
    print 'Couldn\'t read file'
    raise

freq=0

print H.printInfo(None)

print H.getSolsets()
g=H.getSolset('sol000')
print 'Getsoltabs returns',H.getSoltabs(g)

amp=H.getSoltab(g,'amplitude000')
freqs=len(amp.freq)

rms_xx=np.zeros(freqs)
rms_yy=np.zeros(freqs)

for i in range(freqs):
    if (i % 10)==0:
        print i
    rms_xx[i]=np.median(np.std(amp.val[0,0,:,i,:],axis=1))
    rms_yy[i]=np.median(np.std(amp.val[1,0,:,i,:],axis=1))

medrms=0.5*(np.median(rms_xx)+np.median(rms_yy))
scale=2.0

print rms_xx, rms_yy
print 'median value is',medrms

print 'Bad sub-bands:'
bad=[]
for i in range(freqs):
    if rms_xx[i]>scale*medrms or rms_yy[i]>scale*medrms:
        bad.append(i)
print repr(bad)

plt.plot(rms_xx)
plt.plot(rms_yy)
plt.show()
