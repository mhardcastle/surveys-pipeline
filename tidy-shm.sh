#!/bin/bash

ls -l /dev/shm | grep mjh | awk '{print "rm /dev/shm/"$9}' | sh
