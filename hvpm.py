#!/usr/bin/python2.7
#
# Copyright 2017 Google Inc. All Rights Reserved.

"""Interface for a USB-connected HV Monsoon power meter.

(http://msoon.com/LabEquipment/PowerMonitor/).
(https://pypkg.com/pypi/monsoon/f/docs/API.pdf)

  pip install monsoon

"""
import sys
import time
import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op

try:
  from google3.pyglib import flags
except ImportError:
  import gflags as flags  # http://code.google.com/p/python-gflags/

FLAGS = flags.FLAGS


def main(unused_argv):
  """Simple command-line interface for Monsoon."""
  useful_flags = ["voltage", "status", "usbpassthrough", "samples", "current",
                  "startcurrent"]
  if not [f for f in useful_flags if FLAGS.get_flag_value(f, None) is not None]:
    print __doc__.strip()
    print FLAGS.main_module_help()
    return

  if FLAGS.avg and FLAGS.avg < 0:
    print "--avg must be greater than 0"
    return

  mon = HVPM.Monsoon()
  mon.setup_usb()

  if FLAGS.voltage is not None:
    if FLAGS.ramp is not None:
      RampVoltage(mon, 0, FLAGS.voltage)
    else:
      mon.setVout(FLAGS.voltage)

  if FLAGS.status:
    print "Serialno : %d\n" % mon.getSerialNumber();
    mon.fillAllStatusPacket()
    status = mon.statusPacket
    attrs = vars(status)
    print '\n'.join("%s : %s" % item for item in attrs.items())

  if FLAGS.current is not None:
    current = AmpsToApi(FLAGS.current)
    mon.setRunTimeCurrentLimit(current)
    print "Set runtime current to %d" % FLAGS.current

  if FLAGS.startcurrent is not None:
    startcurrent = AmpsToApi(FLAGS.startcurrent)
    mon.setPowerUpCurrentLimit(startcurrent)
    print "Set start current to %d" % FLAGS.startcurrent

  if FLAGS.usbpassthrough:
    if FLAGS.usbpassthrough == "off":
      mon.setUSBPassthroughMode(0)
    elif FLAGS.usbpassthrough == "on":
      mon.setUSBPassthroughMode(1)
    elif FLAGS.usbpassthrough == "auto":
      mon.setUSBPassthroughMode(2)
    else:
      sys.exit("bad passthrough flag: %s" % FLAGS.usbpassthrough)




def RampVoltage(mon, start, end):
  v = start
  if v < 0.8: v = 0.8       # HVPM doesn't support lower than this
  while v < end:
    mon.setVout(v)
    v += .3
  mon.setVout(end)

def AmpsToApi(amps):
  return amps
  #/15.625 * 65535


if __name__ == "__main__":
  # Define flags here to avoid conflicts with people who use us as a library
  flags.DEFINE_boolean("status", None, "Print power meter status")
  flags.DEFINE_integer("avg", None,
                       "Also report average over last n data points")
  flags.DEFINE_float("voltage", None, "Set output voltage (0 for off)")
  flags.DEFINE_integer("current", None, "Set max output current")
  flags.DEFINE_float("startcurrent", None, "Set max power-up/inital current")
  flags.DEFINE_string("usbpassthrough", None, "USB control (on, off, auto)")
  flags.DEFINE_integer("samples", None, "Collect and print this many samples")
  flags.DEFINE_integer("hz", 5000, "Print this many samples/sec")
  flags.DEFINE_integer("serialno", None, "Look for this Monsoon serial number")
  flags.DEFINE_boolean("timestamp", None,
                       "Also print integer (seconds) timestamp on each line")
  flags.DEFINE_boolean("ramp", None, "Gradually increase voltage to prevent "
                       "tripping Monsoon overvoltage")
  flags.DEFINE_list("output", ["main"], "Comma-separated list of sample types "
                    "to output (select from: main, usb, aux, voltage).")
  flags.DEFINE_string("delimiter", " ", "Output delimiter.")

  main(FLAGS(sys.argv))

