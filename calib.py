#!/usr/bin/python

import sys
import config
import os.path
import pyrap.tables as pt
import flagrms

die=config.die
report=config.report
warn=config.warn

if len(sys.argv)<2:
    die('Need a filename for config file')

filename=sys.argv[1]
if not(os.path.isfile(filename)):
    die('Config file does not exist')

if len(sys.argv)<3:
    die('Need a sub-band number')

sb=int(sys.argv[2])
sbs='%03i' % sb

cfg=config.LocalConfigParser()
cfg.read(filename)

unpackpath=cfg.get('paths','unpack')
processedpath=cfg.get('paths','processed')
workpath=cfg.get('paths','work')

croot=cfg.get('files','calibrator')
troot=cfg.get('files','target')

print 'Target is',troot,'calibrator is',croot,'sub-band number is',sbs

run=config.runner(cfg.getoption('control','dryrun',False)).run
cleanup=cfg.getoption('control','cleanup',True)

# Expand this section with required options -- some not implemented yet

antennafix=cfg.getoption('calibration','antennafix',False)
rficonsole=cfg.getoption('calibration','rficonsole',True)
smartdemix=cfg.getoption('calibration','smartdemix',False)
flagib=cfg.getoption('calibration','flagintbaselines',False)
flagbad=cfg.getoption('calibration','flagbadantennas',False)
cra=cfg.getoption('calibration','fitcra',False)

# Now start the calibration

report('Checking directories')

if not(os.path.isdir(workpath)):
    warn('Working directory doesn\'t exist, making it')
    os.makedirs(workpath)

if not(os.path.isdir(processedpath)):
    warn('Final output directory doesn\'t exist, making it')
    os.makedirs(processedpath)

if not(os.path.isdir(unpackpath)):
    die('Path to unpack from doesn\'t exist')

os.chdir(workpath)

report('Unpacking files')

for r in (croot,troot):
    tarfile=unpackpath+'/'+r+'_SB'+sbs+'_uv.dppp.MS.tar'
    if not(os.path.exists(tarfile)):
        die('File to unpack doesn\'t exist -- '+tarfile)
    run('tar xf '+tarfile)

origcms=croot+'_SB'+sbs+'_uv.dppp.MS'
filtercms=croot+'_SB'+sbs+'_uv.filter.MS'
origtms=troot+'_SB'+sbs+'_uv.dppp.MS'
filtertms=troot+'_SB'+sbs+'_uv.filter.MS'

if antennafix:
    report('Fixing the beam info')
    for d in (origcms, origtms):
        run('/soft/fixinfo/fixbeaminfo '+d)

# flag antenna_weight>1

report('Flagging bad antenna weights')
for d in (origcms, origtms):
    run('taql "update '+d+' set FLAG=True where any(WEIGHT_SPECTRUM>1) and ANTENNA1!=ANTENNA2"')

# Here we pass autocorrelations, which should be flagged anyway

if flagib: 
    report('Flagging international baselines')
    open('NDPPP.debug','w').write('Global 5\n')
    for orig,filt in ((origcms,filtercms),(origtms,filtertms)):
        ndppp=open('NDPPP-'+sbs+'.in','w')
        ndppp.write('msin = '+orig+'\n'+
                    'msout = '+filt+'''
steps = [filter]
filter.type = filter
filter.baseline = CS* && RS* ; CS* && CS*; RS* && RS*; RS* && CS*
filter.remove = True
''')
        ndppp.close()
        run('NDPPP NDPPP-'+sbs+'.in')
else:
    run('ln -s '+origcms+' '+filtercms)
    run('ln -s '+origtms+' '+filtertms)

if rficonsole:
    report('Running rficonsole')
    open('rficonsole.debug','w').write('Global 5\n')
    for f in (filtercms,filtertms):
        run('rficonsole -j '+str(config.getcpus())+' '+f)

t = pt.table(filtercms+'/OBSERVATION', readonly=True, ack=False)
calname=t[0]['LOFAR_TARGET'][0]
t.close()

report('Running amplitude calibration')
print 'Calibrator name is',calname
open('bbs-reducer.debug','w').write('Global 5\n')
if cra:
    lines=open('/home/mjh/lofar/text/bbs-transfer-timedep-cra.txt').readlines()
else:
    lines=open('/home/mjh/lofar/text/bbs-transfer-timedep.txt').readlines()
outfile=open('bbs-transfer-'+sbs+'.txt','w')
for l in lines:
    l=l.replace('3C48',calname)
    outfile.write(l)
outfile.close()

calibrated=False
while not(calibrated):
    run('calibrate-stand-alone -f '+filtercms+' bbs-transfer-'+sbs+'.txt /home/mjh/lofar/text/sources-calibrate.txt')

    # We now have a calibrated flux calibrator. Are we flagging?

    if flagbad:
        flaglist=flagrms.flagrms(filtercms)
        if flaglist:
            report('Preparing to flag bad antennas: '+str(flaglist))
            baseline=''
            for f in flaglist:
                baseline+=f+'; '
            baseline=baseline[:-2]
            for data in (filtercms,filtertms):
                ndppp=open('NDPPP-flag-'+sbs+'.in','w')
                ndppp.write('msin = '+data+'\n'+
                            'msout =\n'+
                            'steps = [flag]\nflag.type=preflagger\n'+
                            'flag.baseline='+baseline+'\n')
                ndppp.close()
                run('NDPPP NDPPP-flag-'+sbs+'.in')
            report('Flagging completed, rerun calibration')
        else:
            calibrated=True
    else:
        calibrated=True

report('Gain transfer')
inst=croot+'_SB'+sbs+'.INST'
run('parmexportcal in='+filtercms+'/instrument out='+inst)
run('calibrate-stand-alone -f --parmdb '+inst+' '+filtertms+' /home/mjh/lofar/text/bbs-blank.txt /home/mjh/lofar/text/sources-dummy.txt')

if cleanup:
    report('Cleaning up')
    for data in (filtercms,filtertms):
        run('rsync -av --delete --copy-links '+data+' '+processedpath)

    run('rm -r '+croot+'_SB'+sbs+'*')
    run('rm -r '+troot+'_SB'+sbs+'*')
