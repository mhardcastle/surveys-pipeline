#!/usr/bin/python

# clock-tec preparation: collate the data and assemble the file of solutions

import sys
import config
import os.path

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

croot=cfg.get('files','calibrator')
processedpath=cfg.get('paths','processed')

os.chdir(processedpath)
run=config.runner(cfg.getoption('control','dryrun',False)).run

report('Making the globaldb')

if os.path.isdir('globaldb'):
    run('rm -r globaldb')
run('mkdir globaldb')
os.chdir('globaldb')

sb=0
while sb<366:
    sbs='%03i' % sb
    dir='../'+croot+'_SB'+sbs+'_uv.filter.MS'
    if os.path.isdir(dir):
        break
    sb+=1
else:
    die("Can't find any calibrator files!")

for table in ['ANTENNA','FIELD','sky','OBSERVATION']:
    run('cp -r '+dir+'/'+table+' .')


for i in range(366):
    sbn='%03i' % i
    msname='../'+croot+'_SB'+sbn+'_uv.filter.MS/instrument'
    os.system('ln -s '+msname+' instrument-'+sbn)

report('Importing to hdf5')

os.chdir('..')
run('/home/mjh/git/losoto/tools/H5parm_importer.py -v cal.h5 globaldb')
