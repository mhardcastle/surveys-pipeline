#!/usr/bin/python

# calculate the flux density of a source using the coefficients of a
# polynomial in log space as defined by Scaife & Heald.

import numpy as np

def flux(coeffs,freq,ref=150e6):

    '''
    Calculate the flux density of a source defined using the flux
    coefficients specified in makesourcedb format, i.e. the format used by
    Scaife & Heald. The coefficients (coeffs) are A_i as defined by S&H.
    The frequency (freq) may be one value or a numpy array, in Hz. The
    reference frequency (ref) is 150 MHz by default as in S&H.
    '''

    sf=freq/ref
    f=np.ones_like(freq)*coeffs[0]
    for i,a in enumerate(coeffs[1:]):
        f*=10.0**(a*np.log10(sf)**(i+1))
    return f

if __name__ == '__main__':

    import matplotlib.pyplot as plt
    freq=np.logspace(8,9,30)
    print freq

    c_295=[97.763,-0.582, -0.298, 0.583, -0.363]
    c_286=[27.477,-0.158, 0.032, -0.180]
    c_287=[16.367,-0.364]
    
    c=[c_295,c_286,c_287]

    for cal in c:
        f=flux(cal,freq)
        plt.loglog(freq,f)

    plt.show()
