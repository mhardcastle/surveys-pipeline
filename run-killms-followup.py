#!/usr/bin/python

# find the running or queued killms jobs and submit followup jobs

from subprocess import Popen,PIPE,call

pipe = Popen("qstat", shell=True, stdout=PIPE).stdout

jobs=pipe.readlines()

pipe.close()

for l in jobs:
    if 'killms' in l:
        # found a job
        print l,
        bits=l.split()
        jobid=bits[0]
        pipe=Popen("qstat -f -1 "+jobid, shell=True, stdout=PIPE).stdout
        lines=pipe.readlines()
        pipe.close()
        for sl in lines:
            bits2=sl.split()
            if 'job_array_id' in sl:
                id=bits2[2]

            if 'submit_args' in sl:
                for b in bits2:
                    if 'CONFIG' in b:
                        config=b.replace('CONFIG=','')
        print 'Job id is',id
        print 'Config file is',config
        # cannot use the -t option with dependencies, so fake it up
        command='qsub -W depend=afterok:'+jobid+' -v PBS_ARRAYID='+id+',CONFIG='+config+' -N subtract-image-'+id+' /home/mjh/lofar/surveys-pipeline/subtract_image.qsub'
        print command
        call(command,shell=True)
