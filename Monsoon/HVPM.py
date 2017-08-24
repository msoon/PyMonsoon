import sys
import platform
import time
import socket
import re
import math
import base64

import usb.core
import usb.util
import struct
import Operations as op


import threading
import time
import numpy as np

import pmapi

DEVICE = None
DEVICE_TYPE = None
epBulkWriter = None
epBulkReader = None

Protocol = None
class Monsoon(object):
    def __init__(self, *args, **kwargs):
        self.statusPacket = op.statusPacket
        self.fineThreshold = 64000
        self.auxFineThreshold = 30000
        self.mainvoltageScale = 4
        self.usbVoltageScale = 2
        self.ADCRatio = (float)(62.5 / 1e6); #Each tick of the ADC represents this much voltage
        self.padding = np.zeros(64)
        pass

    def setup_usb(self):
        global DEVICE 
        global DEVICE_TYPE
        global epBulkWriter
        global epBulkReader
        global Protocol


        DEVICE = usb.core.find(idVendor=0x2AB9, idProduct=0x0001)
        # On Linux we need to detach usb HID first
        if "Linux" == platform.system():
            try:
                DEVICE.detach_kernel_driver(0)
            except:
                pass # already unregistered    

        DEVICE.set_configuration()
        cfg = DEVICE.get_active_configuration()
        intf = cfg[(0,0)]

        epBulkWriter = usb.util.find_descriptor(
            intf,
            custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        epBulkReader = usb.util.find_descriptor(
            intf,
            custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

        Protocol = pmapi.USB_protocol(DEVICE)
        #notes are poorly documented, values are:
        #ctrl_transfer(bmRequestType, bmRequest, wValue, wIndex)

    def amps_from_raw(self,raw):
        raw = min(raw,1023)
        result = 8.0*(1.0-(raw/1023.0))
        return result

    def raw_from_amps(self,value):
        result = ((65535-0x0F00) * (value / 15.625)+0x0F00)
        return result

    def setVout(self,value):
        vout = value * op.Conversion.FLOAT_TO_INT
        Protocol.sendCommand(op.OpCodes.setMainVoltage,vout) 
    def setPowerupTime(self,value):
        Protocol.sendCommand(op.OpCodes.setPowerupTime,value)
    def setPowerUpCurrentLimit(self, value):
        value = self.raw_from_amps(value)
        Protocol.sendCommand(op.OpCodes.SetPowerUpCurrentLimit,value)
    def setRunTimeCurrentLimit(self, value):
        value = self.raw_from_amps(value)
        Protocol.sendCommand(op.OpCodes.SetRunCurrentLimit,value)
    def setUSBPassthroughMode(self, USBPassthroughCode):
        Protocol.sendCommand(op.OpCodes.setUsbPassthroughMode,USBPassthroughCode)
    def setVoltageChannel(self, VoltageChannelCode):
        Protocol.sendCommand(op.OpCodes.setVoltageChannel,value)

    def setTemperatureLimit(self,value):
        """Sets the fan turn-on temperature limit.  Only valid in HVPM."""
        raw = self.raw_from_degrees(value)
        Protocol.sendCommand(op.OpCodes.setTemperatureLimit,raw)

    def getSerialNumber(self):
        """Get the device serial number"""
        serialNumber = Protocol.getValue(op.OpCodes.getSerialNumber,2)
        return serialNumber

    def getVoltageChannel(self):
        return(Protocol.getValue(op.OpCodes.setVoltageChannel,1))

    def StartSampling(self,calTime=1250,maxTime=0xFFFFFFFF):
        self.fillStatusPacket()
        Protocol.startSampling(calTime,maxTime)
    def stopSampling(self):
        Protocol.stopSampling()

    def raw_from_degrees(self, value):
        """For setting the fan temperature limit.  Only valid in HVPM."""
        lowbyte = int(math.floor(value))
        highbyte = int(min(0xFF,(value-lowbyte) * 2**8)) #Conversion into Q7.8 format
        raw = struct.unpack("H",struct.pack("BB",highbyte,lowbyte))[0]
        return raw
        

    def degrees_from_raw(self, value):
        """For setting the fan temperature limit.  Only valid in HVPM"""
        value = int(value)
        bytes = struct.unpack("BB",struct.pack("H",value)) #Firmware swizzles these bytes.
        result = bytes[1] + (bytes[0] * 2**-8)
        return result

    def fillStatusPacket(self):

        #Misc Status information.
        self.statusPacket.firmwareVersion = Protocol.getValue(op.OpCodes.FirmwareVersion,2)
        self.statusPacket.protocolVersion = Protocol.getValue(op.OpCodes.ProtocolVersion,2)
        self.statusPacket.temperature = -1 #Not currently supported.
        self.statusPacket.serialNumber = Protocol.getValue(op.OpCodes.getSerialNumber,2)
        self.statusPacket.powerupCurrentLimit = self.amps_from_raw(Protocol.getValue(op.OpCodes.SetPowerUpCurrentLimit,2))
        self.statusPacket.runtimeCurrentLimit = self.amps_from_raw(Protocol.getValue(op.OpCodes.SetRunCurrentLimit,2))
        self.statusPacket.powerupTime = Protocol.getValue(self.setPowerupTime,1)
        self.statusPacket.temperatureLimit = self.degrees_from_raw(Protocol.getValue(op.OpCodes.setTemperatureLimit,2))
        self.statusPacket.usbPassthroughMode = Protocol.getValue(op.OpCodes.setUsbPassthroughMode,1)
        self.statusPacket.hardwareModel = Protocol.getValue(op.OpCodes.HardwareModel,2)

        #Calibration data
        self.statusPacket.mainFineScale = float(Protocol.getValue(op.OpCodes.setMainFineScale,2))
        self.statusPacket.mainCoarseScale = float(Protocol.getValue(op.OpCodes.setMainCoarseScale,2)) 
        self.statusPacket.usbFineScale = float(Protocol.getValue(op.OpCodes.setUSBFineScale,2)) 
        self.statusPacket.usbCoarseScale = float(Protocol.getValue(op.OpCodes.setUSBCoarseScale,2))
        self.statusPacket.auxFineScale = float(Protocol.getValue(op.OpCodes.setAuxFineScale,2))
        self.statusPacket.auxCoarseScale = float(Protocol.getValue(op.OpCodes.setAuxCoarseScale,2))

        self.statusPacket.mainFineZeroOffset = float(Protocol.getValue(op.OpCodes.SetMainFineZeroOffset,2))
        self.statusPacket.mainCoarseZeroOffset = float(Protocol.getValue(op.OpCodes.SetMainCoarseZeroOffset,2))
        self.statusPacket.usbFineZeroOffset = float(Protocol.getValue(op.OpCodes.SetUSBFineZeroOffset,2))
        self.statusPacket.usbCoarseZeroOffset = float(Protocol.getValue(op.OpCodes.SetUSBCoarseZeroOffset,2))


    def BulkRead(self):
        return(DEVICE.read(0x81,64,timeout=0))

    def swizzlePacket(self, packet):
        length = len(packet)
        packet = np.array(packet)
        evenBytes = packet[4::2]
        oddBytes = packet[5::2]
        swizzledBytes = np.insert(evenBytes,np.arange(len(oddBytes)),oddBytes)
        swizzledPacket = np.hstack([packet[0:4],swizzledBytes[:],self.padding[0:(58-length)]])
        swizzledPacket = np.array(swizzledPacket).astype('B')
        packetLength = len(swizzledPacket)
        rawBytes = struct.pack('B'*packetLength,*swizzledPacket)
        measurements = struct.unpack("HBBHHHHHHHHBBHHHHHHHHBBHHHHHHHHBB",rawBytes)
        measurements = list(measurements)
        return measurements





