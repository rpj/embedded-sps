#!/usr/bin/env python

import sys
import time
import signal
import ctypes as ct

class SPS30Measurement(ct.Structure):
    _fields_ = [("mc_1p0", ct.c_float),
                ("mc_2p5", ct.c_float),
                ("mc_4p0", ct.c_float),
                ("mc_10p0", ct.c_float),
                ("nc_0p5", ct.c_float),
                ("nc_1p0", ct.c_float),
                ("nc_2p5", ct.c_float),
                ("nc_4p0", ct.c_float),
                ("nc_10p0", ct.c_float),
                ("typical_particle_size", ct.c_float)]

def sigh(sig, f):
    print "\n\nStop: {}".format(libsps.sps30_stop_measurement())
    sys.exit(sig)

signal.signal(signal.SIGINT, sigh)

libsps = ct.cdll.LoadLibrary("./libsps30.so")

if not libsps:
    print "Couldn't load shared library!"
    sys.exit(-1)

if libsps.sps30_probe() != 0:
    print "Probe failed!"
    sys.exit(-2)

sn = ct.create_string_buffer('\000' * 32)
if libsps.sps30_get_serial(sn) != 0:
    print "Get SN failed!"
    sys.exit(-3)

print "Found SPS30 S/N {}".format(repr(sn.value))
libsps.sps_get_driver_version.restype = ct.c_char_p
print "Driver version: {}".format(libsps.sps_get_driver_version())

aci = ct.c_int()
if libsps.sps30_get_fan_auto_cleaning_interval(ct.byref(aci)) != 0:
    print "Auto-cleaning check failed!"
    sys.exit(-4)

print "Auto-cleaning interval: {} seconds".format(aci.value)

aci = ct.c_byte()
if libsps.sps30_get_fan_auto_cleaning_interval_days(ct.byref(aci)) == 0:
    print "Auto-cleaning interval: {} days".format(aci.value)

if libsps.sps30_start_measurement() != 0:
    print "Couldn't start measuring!"
    sys.exit(-5)

print "Starting up..."
time.sleep(4)

while 1:
    dr = ct.c_byte()
    if libsps.sps30_read_data_ready(ct.byref(dr)) != 0:
        print "Data-ready check failed!"
        sys.exit(-6)
    if bool(dr.value):
        meas = SPS30Measurement()
        if libsps.sps30_read_measurement(ct.byref(meas)) != 0:
            print "Measurement read failed!"
            sys.exit(-7)
        print ""
        print "PM1.0:\t{}".format(meas.mc_1p0)
        print "PM2.5:\t{}".format(meas.mc_2p5)
        print "PM4.0:\t{}".format(meas.mc_4p0)
        print "PM10.0:\t{}".format(meas.mc_10p0)
        print "NC0.5:\t{}".format(meas.nc_0p5)
        print "NC1.0:\t{}".format(meas.nc_1p0)
        print "NC2.5:\t{}".format(meas.nc_2p5)
        print "NC4.0:\t{}".format(meas.nc_4p0)
        print "NC10.0:\t{}".format(meas.nc_10p0)
        print "TypSz:\t{}".format(meas.typical_particle_size)
    time.sleep(2)

sigh(0, None)
