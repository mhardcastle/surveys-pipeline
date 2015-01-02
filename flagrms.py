#!/usr/bin/python

# Flag high-rms antennae

import pyrap.tables as pt
import numpy as np

def flagrms(rootname,threshold=9):

    t = pt.table(rootname+'/ANTENNA', readonly=True, ack=False)
#antennaname=pt.tablecolumn(t,'NAME')
    antennaname=list(t.col('NAME'))
    t.close()
    an=len(antennaname)
    print 'There are',an,'antennas'

    t=pt.table(rootname, readonly=True, ack=False)
    xxm=np.zeros(an)
    yym=np.zeros(an)
    xxrms=np.zeros(an)
    yyrms=np.zeros(an)
    for i,ant in enumerate(antennaname):

        newt=pt.taql('select CORRECTED_DATA,FLAG from $t where ANTENNA1=$i or ANTENNA2=$i')
        channels,corrs=np.shape(newt[0]['CORRECTED_DATA'])

        xx=newt.getcol('CORRECTED_DATA')[:,:,0]
        yy=newt.getcol('CORRECTED_DATA')[:,:,3]
        fxx=np.logical_not(newt.getcol('FLAG'))[:,:,0]
        fyy=np.logical_not(newt.getcol('FLAG'))[:,:,3]
        axx=np.abs(xx)
        ayy=np.abs(yy)
        xxm[i]=abs(np.mean(axx[fxx]))
        yym[i]=abs(np.mean(ayy[fyy]))
        xxrms[i]=np.std(axx[fxx])
        yyrms[i]=np.std(ayy[fyy])
        print i,ant,xxm[i],yym[i],xxrms[i],yyrms[i]

    fsum=(xxm+yym)/2.0
    rmsum=(xxrms+yyrms)/2.0
    fmed=np.median(fsum)
    rmmed=np.median(rmsum)
    badness=fsum*rmsum/rmmed/fmed
    flaglist=[]
    for i,ant in enumerate(antennaname):
        print i,antennaname[i],fsum[i]/fmed,rmsum[i]/rmmed,badness[i],'Flag' if (badness[i]>threshold) else ''
        if badness[i]>threshold:
            flaglist.append(antennaname[i])

    return flaglist

