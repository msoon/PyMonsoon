"""Tests for google3.third_party.py.Monsoon"""

from google3.testing.pybase import googletest
from google3.third_party.py.Monsoon import LVPM
from google3.third_party.py.Monsoon import Operations as op
from google3.third_party.py.Monsoon import sampleEngine
from google3.third_party.py.Monsoon.pmapi import USB_protocol

import usb.util as util

MONSOON_VENDOR_ID = 0x2AB9
MONSOON_PRODUCT_ID = 0x0001
BUFFER_SIZE = 64
SERIAL_NO = 20225

class MockUSBDevice(googletest.DoNothing):
  def __init__(self):
    self.idVendor = MONSOON_VENDOR_ID
    self.idProduct = MONSOON_PRODUCT_ID
    self.iSerialNumber = SERIAL_NO

class MockUSBProtocol(googletest.DoNothing):

  def __init__(self):
    self.DEVICE = MockUSBDevice()

  def Connect(self, deviceType, serialno=None):
    #do nothing
    return

  def BulkRead(self):
    return util.create_buffer(BUFFER_SIZE)

  def sendCommand(self, operation, value):
    #do nothing
    return

  def getValue(self, operation, valueLength):
    if (operation == op.OpCodes.getSerialNumber):
      return SERIAL_NO

class MonsoonTest(googletest.TestCase):
  # TODO: Add more unit tests
  def testValidateSerialNo(self):
    mock = MockUSBProtocol()
    monsoon = LVPM.Monsoon()
    monsoon.setup_usb(SERIAL_NO, mock)
    self.assertEqual(monsoon.getSerialNumber(), SERIAL_NO)

  def testSetInvalidVoltage(self):
    mock = MockUSBProtocol()
    monsoon = LVPM.Monsoon()
    monsoon.setup_usb(SERIAL_NO, mock)
    with self.assertRaises(Exception):
      monsoon.setVout(1.0)

if __name__ == '__main__':
  googletest.main()
