import sys
import platform
import time
import socket
import re
import base64

import usb.core
import usb.util
import struct
import Operations as op
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
        self.fineThreshold = 30000
        self.auxFineThreshold = 30000
        self.mainvoltageScale = 2
        self.usbVoltageScale = 2
        self.ADCRatio = (float)(62.5 / 1e6); #Each tick of the ADC represents this much voltage
        self.factoryRes = 0.050
        self.auxFactoryResistor = 0.1
        self.__padding = np.zeros(64)
        pass

    def setup_usb(self):
        global DEVICE 
        global DEVICE_TYPE
        global epBulkWriter
        global epBulkReader
        global Protocol
        DEVICE = usb.core.find(idVendor=0x2AB9, idProduct=0x0001)
        if DEVICE is None:
            print("Error: could not find device")
            pass

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
        
    


    def __amps_from_raw(self,raw):
        """Translate EEPROM overcurrent protection value setting into amps."""
        raw = min(raw,1023)
        result = 8.0*(1.0-(raw/1023.0))
        return result

    def __raw_from_amps(self,value):
        """Translate amp setting for overcurrent protection into EEPROM value"""
        result = 1023 * (1.0 - (amps/8.0))
        return result


    def setVout(self,value):
        """Set Vout.  Valid values from 2.01-4.55.  0 = turn off."""
        if(value > 2.00 and value < 4.56 or value == 0):
            vout = value * op.Conversion.FLOAT_TO_INT
            Protocol.sendCommand(op.OpCodes.setMainVoltage,vout) 
        else:
            raise Exception("Invalid Voltage value")

    def setPowerupTime(self,value):
        """time in ms where powerupcurrentlimit applies, vs runtimecurrentlimit"""
        Protocol.sendCommand(op.OpCodes.setPowerupTime,value)

    def setPowerUpCurrentLimit(self, value):
        """Sets power up current limit.  Valid values are 0-8 Amps"""
        value = self.__raw_from_amps(value)
        Protocol.sendCommand(op.OpCodes.SetPowerUpCurrentLimit,value)

    def setRunTimeCurrentLimit(self, value):
        """Sets runtime current limit.  Valid values are 0-8 amps."""
        value = self.__raw_from_amps(value)
        Protocol.sendCommand(op.OpCodes.SetRunCurrentLimit,value)

    def setUSBCoarseZeroOffset(self,value):
        """Zero offset, not used in LVPM"""
        Protocol.sendCommand(op.OpCodes.SetUSBCoarseZeroOffset,value)

    def setUSBPassthroughMode(self, USBPassthroughCode):
        """USB Passthrough mode.  0 = off, 1 = on, 2 = auto"""
        Protocol.sendCommand(op.OpCodes.setUsbPassthroughMode,USBPassthroughCode)

    def setVoltageChannel(self, VoltageChannelCode):
        """Sets voltage measurement channel.  0 = Main & USB, 1 = Main & Aux"""
        Protocol.sendCommand(op.OpCodes.setVoltageChannel,value)

    def getVoltageChannel(self):
        """0 = Main & USB, 1 = Main & Aux"""
        return(Protocol.getValue(op.OpCodes.setVoltageChannel,1))
    def getSerialNumber(self):
        """Get the device serial number"""
        serialNumber = Protocol.getValue(op.OpCodes.getSerialNumber,2)
        return serialNumber

    def fillStatusPacket(self):
        """Get all calibration information from the device EEPROM"""
        self.statusPacket.mainFineResistorOffset = float(Protocol.getValue(op.OpCodes.setMainFineResistorOffset,1))
        mainFineResistor = self.factoryRes + self.statusPacket.mainFineResistorOffset * 0.0001
        self.statusPacket.mainCoarseResistorOffset = float(Protocol.getValue(op.OpCodes.setMainCoarseResistorOffset,1))
        mainCoarseResistor = self.factoryRes + self.statusPacket.mainCoarseResistorOffset * 0.0001
        self.statusPacket.usbFineResistorOffset = float(Protocol.getValue(op.OpCodes.setUsbFineResistorOffset,1))
        usbFineResistor = self.factoryRes + self.statusPacket.usbFineResistorOffset * 0.0001
        self.statusPacket.usbCoarseResistorOffset = float(Protocol.getValue(op.OpCodes.setUsbCoarseResistorOffset,1))
        usbCoarseResistor = self.factoryRes + self.statusPacket.usbCoarseResistorOffset * 0.0001
        self.statusPacket.auxFineResistorOffset = float(Protocol.getValue(op.OpCodes.setAuxFineResistorOffset,1))
        auxFineResistor = self.auxFactoryResistor + self.statusPacket.auxFineResistorOffset * 0.0001
        self.statusPacket.auxCoarseResistorOffset = float(Protocol.getValue(op.OpCodes.setAuxCoarseResistorOffset,1))
        auxCoarseResistor = self.auxFactoryResistor + self.statusPacket.auxCoarseResistorOffset * 0.0001

        
        self.statusPacket.mainFineScale = 35946.0 * (self.factoryRes / mainFineResistor)
        self.statusPacket.mainCoarseScale = 3103.4 * (self.factoryRes / mainCoarseResistor)
        self.statusPacket.usbFineScale = 35946.0 * (self.factoryRes / usbFineResistor)
        self.statusPacket.usbCoarseScale = 3103.4 * (self.factoryRes / usbCoarseResistor)
        self.statusPacket.auxFineScale = 0.05049 * (self.auxFactoryResistor / auxFineResistor)
        self.statusPacket.auxCoarseScale = 1.289 * (self.auxFactoryResistor / auxCoarseResistor)

        self.statusPacket.mainFineZeroOffset = 0
        self.statusPacket.mainCoarseZeroOffset = 0
        self.statusPacket.usbFineZeroOffset = 0
        self.statusPacket.usbCoarseZeroOffset = 0

    def StartSampling(self,calTime=1250,maxTime=0xFFFFFFFF):
        self.fillStatusPacket()
        Protocol.startSampling(calTime,maxTime)

    def stopSampling(self):
        Protocol.stopSampling()
        #ctrl_transfer(bmRequestType, bmRequest, wValue, wIndex)
    def BulkRead(self):
        """Read a sample packet"""
        return(DEVICE.read(0x81,64,timeout=0))

    def swizzlePacket(self, packet):
        """Byte order for 2-byte values is swapped for the majority of the measurement packet.  This fixes that."""
        length = len(packet)
        packet = np.array(packet)
        evenBytes = packet[4::2]
        oddBytes = packet[5::2]
        swizzledBytes = np.insert(evenBytes,np.arange(len(oddBytes)),oddBytes)
        swizzledPacket = np.hstack([packet[0:4],swizzledBytes[:],self.__padding[0:(58-length)]])
        swizzledPacket = np.array(swizzledPacket).astype('b')
        packetLength = len(swizzledPacket)
        rawBytes = struct.pack('b'*packetLength,*swizzledPacket)
        measurements = struct.unpack("HBBhhhhhhhHBBhhhhhhhHBBhhhhhhhHBB",rawBytes)
        measurements = list(measurements)
        return measurements





