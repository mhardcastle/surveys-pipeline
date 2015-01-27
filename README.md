surveys-pipeline
----------------

This is the code for my pipeline designed to do a complete end-to-end
reduction of LOFAR data taken in 'surveys' mode on a Torque/PBS
cluster. It relies on standard LOFAR software and astropy.

*** At the time of writing this is not a complete package -- some
*** utilities and files are missing and paths are dependent on local
*** architecture. Please do not expect to be able to run it out of the box.

Starting assumptions:

-- you have a dataset with a short flux calibrator observation and a
   long observation on-source. (Secondary calibrator observations, if
   present, are not used.)

-- you have a Torque/PBS cluster with the standard LOFAR software
   installed. (Details of the qsub files are Herts-specific and will
   need to be adapted.)

-- you want to image the full field of view and are happy to achieve
   an off-source noise around 300 microJy/beam at ~ 20 arcsec
   resolution. (Higher resolutions have not been tested.)

The basic approach is as follows (commands for each step are given below):

0. A config file is used to control all aspects of the pipeline
   (example.cfg shows the syntax).

1. We load in and flag the individual sub-bands for the calibrator and
   source (calib.py, run-calib.qsub). Various types of flagging can be
   applied at this point. The gain is then estimated from the
   calibrator observation, and, once all noisy antennas are removed,
   the gain is transferred from the calibrator to the source (note
   that GAIN TRANSFER DOES NOT WORK PROPERLY FOR LOFAR at the time of
   writing -- this code will need to be changed when a fix is
   available). The final phases are also transferred, which mitigates
   the effect of clock errors. (We do not fit for common rotation
   angle as using this for gain transfer actually makes the results
   worse.) The filtered data are written out ready for the next stage.

2. The data are amalgamated into 'bands' of 10 sb each. From now on,
   we only use those bands (makeband.py).

3. We now need to bootstrap an acceptable sky model. This has to be
   done to some extent by hand:

   * generate a GSM sky model with standard utility gsm.py
   * image the band 20 dataset at 45-arcsec resolution
   * make a catalog with PyBDSM
   * cross-match the catalog with the NVSS catalog to get accurate
     positions and source structures. (This step ensures that no
     artefacts are included in your sky model, at the cost of
     excluding any steep-spectrum sources. However, there are
     sufficiently few of those that it does not seem likely to cause a
     problem.)
   * this crossmatch, with LOFAR fluxes but NVSS positions and source
     structures, is your new sky model.

   (Note that it is possible to do the crossmatch by making a
   high-resolution initial image and cross-matching with FIRST
   instead, if you happen to be in the right part of the sky. This is
   likely to work better if you are aiming for something close to the
   full resolution of the dataset.)

4. We phase-calibrate all the bands using this sky model.
   (apply-nvss-skymodel.py, apply-nvss-skymodel.qsub)

5. We image all the bands with this calibration, applying the beam.
   Optionally we do a two-stage process where we image, make a mask,
   and image again to attempt to circumvent the standard clean
   convergence problems with artefacts around bright sources.

6. At this point the imaging is complete. makecat.py will convolve all
   the images to a common resolution and generate a catalogue from the
   combined image.

7. Optionally, direction-dependent effects can be taken into account
   using Cyril Tasse's CoJones package (formerly killMS). To do this,
   we take the unmasked output of the images for the bands in section
   5 and make a catalogue for them using PyBDSM
   (make-band-cat.py,.qsub). We take the bright sources from this
   catalogue and subtract them from the data with CoJones (killms.py,
   killms.qsub). Then we re-image with subtract_image.py (.qsub) and
   optionally restore the subtracted Gaussians (restore.py, .qsub).
   The final images may be combined and catalogued with makecat.py . 

Detailed example command list:
------------------------------

Torque commands use the job array feature -- each sub-band is a
separate job (and so can be run on a separate node).

Here I describe the process where you calibrate all the data. For a
quick look, calibrate only sub-bands 200-209 to start with and make
and image band 20, then go back and calibrate all the other sub-bands

1. qsub -t 0-366 -v CONFIG=/home/mjh/lofar/surveys-pipeline/example.cfg ~/lofar/surveys-pipeline/run-calib.qsub

2. makeband.py /home/mjh/lofar/surveys-pipeline/example.cfg 0 36
   (ideally run on the file server)

3. Here for simplicity I give the files short names: the actual names
   will be derived from the LOFAR observation ID.
   gsm.py xxx yyy 4.5 gsm.skymodel
   calibrate-stand-alone -f B20.concat.MS /home/mjh/lofar/text/bbs-phaseonly gsm.skymodel
   ctod.py B20.concat.MS B20.image.MS
   applybeam.py B20.image.MS
   awimager ms=B20.image.MS image=B20-img-45 weight=briggs robust=0 npix=2048 cellsize=12arcsec data=CORRECTED padding=1.3 niter=400000 stokes=I operation=mfclark UVmin=0.1 UVmax=4.6 wmax=9000 threshold=0.01Jy
   tofits.py B20-img-45.restored B20-img-45.restored.corr
   blanker.py B20-img-45.restored.fits B20-img-45.restored.corr.fits

   pybdsm
   inp process_image
   filename='B20-img-45.restored.corr.fits'
   mean_map='zero'
   rms_map=True
   advanced_opts=True
   detection_image='B20-img-45.restored.fits'
   rms_box=(55,12)
   adaptive_rms_box=True
   adaptive_thresh=150
   rms_box_bright=(80,20)
   go
   inp write_catalog
   catalog_type='gaul'
   go

   I do crossmatching with STILTS:

   /soft/topcat/stilts tmatch2 matcher=sky params=30 values1="RA DEC" values2="RA DEC" L246353_B20-img-45.restored.corr.pybdsm.gaul.fits /stri-data/mjh/NVSS/CATALOG41.FIT out=crossmatch.fits

   At this point move the old band 20 images etc out of the way, as
   they will be overwritten by the next step.

4. qsub -t 0-36 -v CONFIG=/home/mjh/lofar/surveys-pipeline/example.cfg apply-nvss-skymodel.qsub

5. qsub -t 0-36 -v CONFIG=/home/mjh/lofar/surveys-pipeline/example.cfg image.qsub

6. makecat.py example.cfg

7. qsub -t 0-36 -v CONFIG=/home/mjh/lofar/surveys-pipeline/example.cfg make-band-cat.qsub
   qsub -t 0-36 -v CONFIG=/home/mjh/lofar/surveys-pipeline/example.cfg killms.qsu
   qsub -t 0-36 -v CONFIG=/home/mjh/lofar/surveys-pipeline/example.cfg subtract-image.qsub
   qsub -t 0-36 -v CONFIG=/home/mjh/lofar/surveys-pipeline/example.cfg restore.qsub

