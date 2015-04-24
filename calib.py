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
notransfer=cfg.getoption('calibration','notransfer',False)
notarget=cfg.getoption('calibration','notarget',False)
cep1format=cfg.getoption('calibration','cep1format',False)
flagbadweight=cfg.getoption('calibration','flagbadweight',True)
skipexisting=cfg.getoption('calibration','skip_existing',False)

try:
    calibskymodel=cfg.get('calibration','skymodel')
    calibrator_skymodel=True
    print 'Using sky model',calibskymodel
except:
    calibskymodel='/home/mjh/lofar/text/sources-calibrate.txt'
    calibrator_skymodel=False

# Now start the calibration

report('Checking directories')

if not(os.path.isdir(workpath)):
    warn('Working directory doesn\'t exist, making it')
    # catch race
    try:
        os.makedirs(workpath)
    except OSError:
        pass
    if not(os.path.isdir(workpath)):
        die('Could not make working directory')

if not(os.path.isdir(processedpath)):
    warn('Final output directory doesn\'t exist, making it')
    try:
        os.makedirs(processedpath)
    except OSError:
        pass
    if not(os.path.isdir(processedpath)):
        die('Could not make output directory')

if not(os.path.isdir(unpackpath)):
    die('Path to unpack from doesn\'t exist')

origcms=croot+'_SB'+sbs+'_uv.dppp.MS'
filtercms=croot+'_SB'+sbs+'_uv.filter.MS'
origtms=troot+'_SB'+sbs+'_uv.dppp.MS'
filtertms=troot+'_SB'+sbs+'_uv.filter.MS'

if skipexisting:
    report('Inspecting output directory for existing files')
    if os.path.isdir(processedpath+'/'+filtercms) and os.path.isdir(processedpath+'/'+filtertms):
        die('Output data already exist, will not over-write them')

os.chdir(workpath)

report('Unpacking files')

if notarget:
    unpack=(croot,)
else:
    unpack=(croot,troot)

if cep1format:
    for r in unpack:
        oldname=unpackpath+'/'+r+'/'+r+'_SAP000_SB'+sbs+'_uv.MS.dppp'
        newname=r+'_SB'+sbs+'_uv.dppp.MS'
        run('cp -r '+oldname+' '+newname)
else:
    for r in unpack:
        tarfile=unpackpath+'/'+r+'_SB'+sbs+'_uv.dppp.MS.tar'
        if not(os.path.exists(tarfile)):
            die('File to unpack doesn\'t exist -- '+tarfile)
        run('tar xf '+tarfile)

if notarget:
    orign=(origcms,)
    filtr=(filtercms,)
else:
    orign=(origcms,origtms)
    filtr=(filtercms,filtertms)

if antennafix:
    report('Fixing the beam info')
    for d in orign:
        run('/soft/fixinfo/fixbeaminfo '+d)

# flag antenna_weight>1
if flagbadweight:
    report('Flagging bad antenna weights')
    for d in orign:
        run('taql "update '+d+' set FLAG=True where any(WEIGHT_SPECTRUM>1) and ANTENNA1!=ANTENNA2"')

# Here we pass autocorrelations, which should be flagged anyway

if flagib: 
    report('Flagging international baselines')
    open('NDPPP.debug','w').write('Global 5\n')
    for orig,filt in zip(orign,filtr):
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
    if not(notarget):
        run('ln -s '+origtms+' '+filtertms)

# now do preflagging if required

preflag=True
try:
    preflag_sb=cfg.get('preflag','sbrange')
    preflag_ants=cfg.get('preflag','antenna')
    bits=preflag_sb.split(',')
    sbmin=int(bits[0])
    sbmax=int(bits[1])
    preflag_slist=[[sbmin,sbmax],]
    preflag_antlist=[preflag_ants,]
    
except config.NoOptionError:
    try:
        preflag_slist=eval(cfg.get('preflag','sblist'))
        preflag_antlist=eval(cfg.get('preflag','antlist'))
    except config.NoOptionError:
        preflag=False

if preflag:
    report('Preflagging')
    preflag_ants=None
    for i,r in enumerate(preflag_slist):
        sbmin,sbmax=r
        if sb>=sbmin and sb<=sbmax:
            preflag_ants=preflag_antlist[i]
    if preflag_ants is not None:
        report('This dataset is in the range to be flagged')
        for ms in filtr:
            ndppp=open('NDPPP-'+sbs+'.in','w')
            ndppp.write('msin='+ms+'''
msout=.
steps=[flag]
flag.type=preflagger
''')
            ndppp.write('flag.baseline=['+preflag_ants+']\n')
            ndppp.close()
            run('NDPPP NDPPP-'+sbs+'.in')

if rficonsole:
    report('Running rficonsole')
    open('rficonsole.debug','w').write('Global 5\n')
    for f in filtr:
        run('rficonsole -j '+str(config.getcpus())+' '+f)

t = pt.table(filtercms+'/OBSERVATION', readonly=True, ack=False)
calname=t[0]['LOFAR_TARGET'][0]
t.close()

report('Running amplitude calibration')
print 'Calibrator name is',calname
if calibrator_skymodel:
    # we assume this is a sky model for the calibrator, so all sources should be used.
    calname=''
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
    run('calibrate-stand-alone -f '+filtercms+' bbs-transfer-'+sbs+'.txt '+calibskymodel)

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

if not(notransfer):
    report('Gain transfer')
    inst=croot+'_SB'+sbs+'.INST'
    run('parmexportcal in='+filtercms+'/instrument out='+inst)
    run('calibrate-stand-alone -f --parmdb '+inst+' '+filtertms+' /home/mjh/lofar/text/bbs-blank.txt /home/mjh/lofar/text/sources-dummy.txt')

if cleanup:
    report('Cleaning up')
    for data in filtr:
        run('rsync -av --delete --copy-links '+data+' '+processedpath)

    run('rm -r '+croot+'_SB'+sbs+'*')
    if not(notarget):
        run('rm -r '+troot+'_SB'+sbs+'*')
