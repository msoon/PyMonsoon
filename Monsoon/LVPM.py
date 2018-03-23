import platform

import usb.core
import usb.util
import struct
from Monsoon import Operations as op

import numpy as np
from Monsoon import pmapi



class Monsoon(object):

    def __init__(self, *args, **kwargs):
        self.DEVICE = None
        self.DEVICE_TYPE = None
        self.epBulkWriter = None
        self.epBulkReader = None
        self.Protocol = None
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

    def enumerateDevices(self):
        temp = pmapi.USB_protocol()
        return temp.enumerateDevices()
    def closeDevice(self):
        self.Protocol.closeDevice();

    def setup_usb(self, serialno = None, Protocol=pmapi.USB_protocol()):
        Protocol.Connect(op.HardwareModel.LVPM,serialno)
        self.Protocol = Protocol


    def amps_from_raw(self,raw):
        """Translate EEPROM overcurrent protection value setting into amps."""
        raw = min(raw,1023)
        result = 8.0*(1.0-(raw/1023.0))
        return result

    def raw_from_amps(self,amps):
        """Translate amp setting for overcurrent protection into EEPROM value"""
        result = 1023 * (1.0 - (amps/8.0))
        return result


    def setVout(self,value):
        """Set Vout.  Valid values from 2.01-4.55.  0 = turn off."""
        if(value > 2.00 and value < 4.56 or value == 0):
            vout = value * op.Conversion.FLOAT_TO_INT
            self.Protocol.sendCommand(op.OpCodes.setMainVoltage,vout)
        else:
            raise Exception("Invalid Voltage value")

    def setPowerupTime(self,value):
        """time in ms where powerupcurrentlimit applies, vs runtimecurrentlimit"""
        self.Protocol.sendCommand(op.OpCodes.setPowerupTime,value)

    def setPowerUpCurrentLimit(self, value):
        """Sets power up current limit.  Valid values are 0-8 Amps"""
        value = self.__raw_from_amps(value)
        self.Protocol.sendCommand(op.OpCodes.SetPowerUpCurrentLimit,value)

    def setRunTimeCurrentLimit(self, value):
        """Sets runtime current limit.  Valid values are 0-8 amps."""
        value = self.__raw_from_amps(value)
        self.Protocol.sendCommand(op.OpCodes.SetRunCurrentLimit,value)

    def setUSBCoarseZeroOffset(self,value):
        """Zero offset, not used in LVPM"""
        self.Protocol.sendCommand(op.OpCodes.SetUSBCoarseZeroOffset,value)

    def setUSBPassthroughMode(self, USBPassthroughCode):
        """USB Passthrough mode.  0 = off, 1 = on, 2 = auto"""
        self.Protocol.sendCommand(op.OpCodes.setUsbPassthroughMode,USBPassthroughCode)

    def setVoltageChannel(self, VoltageChannelCode):
        """Sets voltage measurement channel.  0 = Main & USB, 1 = Main & Aux"""
        self.Protocol.sendCommand(op.OpCodes.setVoltageChannel,VoltageChannelCode)

    def getVoltageChannel(self):
        """0 = Main & USB, 1 = Main & Aux"""
        return(self.Protocol.getValue(op.OpCodes.setVoltageChannel,1))
    def getSerialNumber(self):
        """Get the device serial number"""
        serialNumber = self.Protocol.getValue(op.OpCodes.getSerialNumber,2)
        return serialNumber
    def setDefaultScaleValues(self):
        """Not implemented for LVPM yet"""
        raise NotImplementedError
    def fillStatusPacket(self):
        """Get all calibration information from the device EEPROM"""

        #Misc Status information.
        self.statusPacket.firmwareVersion = self.Protocol.getValue(op.OpCodes.FirmwareVersion,2)
        self.statusPacket.protocolVersion = self.Protocol.getValue(op.OpCodes.ProtocolVersion,1)
        self.statusPacket.temperature = -1 #Not currently supported.
        self.statusPacket.serialNumber = self.Protocol.getValue(op.OpCodes.getSerialNumber,2)
        self.statusPacket.powerupCurrentLimit = self.amps_from_raw(self.Protocol.getValue(op.OpCodes.SetPowerUpCurrentLimit,2))
        self.statusPacket.runtimeCurrentLimit = self.amps_from_raw(self.Protocol.getValue(op.OpCodes.SetRunCurrentLimit,2))
        self.statusPacket.powerupTime = self.Protocol.getValue(op.OpCodes.setPowerupTime,1)
        self.statusPacket.usbPassthroughMode = self.Protocol.getValue(op.OpCodes.setUsbPassthroughMode,1)
        self.statusPacket.hardwareModel = self.Protocol.getValue(op.OpCodes.HardwareModel,2)

        #Calibration data
        self.statusPacket.mainFineResistorOffset = float(self.Protocol.getValue(op.OpCodes.setMainFineResistorOffset,1))
        mainFineResistor = self.factoryRes + self.statusPacket.mainFineResistorOffset * 0.0001
        self.statusPacket.mainCoarseResistorOffset = float(self.Protocol.getValue(op.OpCodes.setMainCoarseResistorOffset,1))
        mainCoarseResistor = self.factoryRes + self.statusPacket.mainCoarseResistorOffset * 0.0001
        self.statusPacket.usbFineResistorOffset = float(self.Protocol.getValue(op.OpCodes.setUsbFineResistorOffset,1))
        usbFineResistor = self.factoryRes + self.statusPacket.usbFineResistorOffset * 0.0001
        self.statusPacket.usbCoarseResistorOffset = float(self.Protocol.getValue(op.OpCodes.setUsbCoarseResistorOffset,1))
        usbCoarseResistor = self.factoryRes + self.statusPacket.usbCoarseResistorOffset * 0.0001
        self.statusPacket.auxFineResistorOffset = float(self.Protocol.getValue(op.OpCodes.setAuxFineResistorOffset,1))
        auxFineResistor = self.auxFactoryResistor + self.statusPacket.auxFineResistorOffset * 0.0001
        self.statusPacket.auxCoarseResistorOffset = float(self.Protocol.getValue(op.OpCodes.setAuxCoarseResistorOffset,1))
        auxCoarseResistor = self.auxFactoryResistor + self.statusPacket.auxCoarseResistorOffset * 0.0001

        #LVPM Scaling system.
        self.statusPacket.mainFineScale = 35946.0 * (self.factoryRes / mainFineResistor)
        self.statusPacket.mainCoarseScale = 3103.4 * (self.factoryRes / mainCoarseResistor)
        self.statusPacket.usbFineScale = 35946.0 * (self.factoryRes / usbFineResistor)
        self.statusPacket.usbCoarseScale = 3103.4 * (self.factoryRes / usbCoarseResistor)
        self.statusPacket.auxFineScale = 0.05049 * (self.auxFactoryResistor / auxFineResistor)
        self.statusPacket.auxCoarseScale = 1.289 * (self.auxFactoryResistor / auxCoarseResistor)

        #LVPM units don't use zero offset information.
        self.statusPacket.mainFineZeroOffset = 0
        self.statusPacket.mainCoarseZeroOffset = 0
        self.statusPacket.usbFineZeroOffset = 0
        self.statusPacket.usbCoarseZeroOffset = 0

    def StartSampling(self,calTime=1250,maxTime=0xFFFFFFFF):
        self.fillStatusPacket()
        self.Protocol.startSampling(calTime,maxTime)

    def stopSampling(self):
        self.Protocol.stopSampling()
        #ctrl_transfer(bmRequestType, bmRequest, wValue, wIndex)
    def BulkRead(self):
        """Read sample packets.
        Returns an array of 64 byte packets concatenated together.
        Number of packets depends on the protocol selected."""
        return self.Protocol.BulkRead()

    def swizzlePacket(self, packet):
        """Byte order for 2-byte values is swapped for the majority of the measurement packet.  This fixes that."""
        length = len(packet)
        packet = np.array(packet)
        evenBytes = packet[4::2]
        oddBytes = packet[5::2]
        swizzledBytes = np.insert(evenBytes,np.arange(len(oddBytes)),oddBytes)
        swizzledPacket = np.hstack([packet[0:4],swizzledBytes[:],self.__padding[0:(58-length)]])
        swizzledPacket = np.array(swizzledPacket).astype('b')
        swizzledPacket = swizzledPacket[0:58]
        packetLength = len(swizzledPacket)
        rawBytes = struct.pack('b'*packetLength,*swizzledPacket)
        measurements = struct.unpack("HBBhhhhhhHHBBhhhhhhhHBBhhhhhhhHBB",rawBytes)
        measurements = list(measurements)
        return measurements

    def Reconnect(self):
        self.Protocol.reconnect(op.HardwareModel.LVPM,self.statusPacket.serialNumber)
    def resetToBootloader(self):
        #Generally not supported by LVPM units.
        self.Protocol.resetToBootloader()



