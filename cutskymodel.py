#!/usr/bin/python

# filter a sky model made from the band maps -- for insertion into killms

import sys

filename=sys.argv[1]
flux=float(sys.argv[2])

outname=filename+'.filtered'

infile=open(filename)
outfile=open(outname,'w')

for l in infile.readlines():
    if 'format' in l:
        outfile.write(l+'\n')
    else:
        bits=l.split(', ')
        if len(bits)>10 and float(bits[4])>=flux:
            outfile.write(l)

outfile.close()
infile.close()
