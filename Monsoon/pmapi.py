import struct
from Monsoon import Operations as op
import ctypes
import platform
import usb.core
import usb.util
import numpy as np
import os
import platform
import time

class USB_protocol(object):
    """Uses native python usb functions to communicate with the Power Monitor.
    Best choice for connecting to a single Power Monitor."""
    def __init__(self):
        self.DEVICE = None

    def enumerateDevices(self):
        """Returns a list of the serial numbers of all devices connected to the system.
        Includes both HVPM LVPM hardware"""
        results = []
      
        devices = usb.core.find(find_all=True, idVendor = 0x2AB9, idProduct = 0x0001)
        for device in devices:
            results.append(str(device.serial_number))
        return results

    def reconnect(self,deviceType, serialno):
        """Reset the port and reconnect to the power monitor.
        Useful for some cases"""
        self.DEVICE.reset()
        time.sleep(5)
        #give device time to re-enumerate
        #TODO:  We should be able to replace this with waiting for the event that fires when
        #A new device enumerates on the system.
        self.Connect(deviceType,serialno)

    def Connect(self,deviceType, serialno=None):
        """Connect to a Power Monitor.
        deviceType = LVPM or HVPM
        serialno = device serial number.  If None, connect to the first device found"""

        def device_matcher(d):
            try:
                return d.idVendor == 0x2AB9 and d.idProduct == 0x0001 and (serialno is None or d.serial_number == str(serialno))
            except:#Catches some platform-specific errors when connecting to multiple PMs simultaneously.
                return False
        self.DEVICE = usb.core.find(custom_match=device_matcher)
        if (self.DEVICE is None):
            print('Unable to find device')
            return
        connectedDeviceType = self.getValue(op.OpCodes.HardwareModel,2)
        if(connectedDeviceType != deviceType):
            print('warning:  Device type mismatch.  Found ' + repr(connectedDeviceType) + " expected " + repr(deviceType))
        firmwareRev = self.getValue(op.OpCodes.FirmwareVersion,1)
        if(firmwareRev < op.ReturnCodes.CURRENT_FIRMWARE_REV):
            print('Warning:  Detected firmware revision ' + repr(firmwareRev) + ", current release is " + repr(op.ReturnCodes.CURRENT_FIRMWARE_REV))
        # On Linux we need to detach usb HID first
        if "Linux" == platform.system():
            try:
                self.DEVICE.detach_kernel_driver(0)
            except:
                pass # already unregistered

        self.DEVICE.set_configuration()
        cfg = self.DEVICE.get_active_configuration()
        intf = cfg[(0,0)]
        self.epBulkWriter = usb.util.find_descriptor(
            intf,
            custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_OUT)
        self.epBulkReader = usb.util.find_descriptor(
            intf,
            custom_match = \
                lambda e: \
                usb.util.endpoint_direction(e.bEndpointAddress) == \
                usb.util.ENDPOINT_IN)

    def BulkRead(self):
        return(self.DEVICE.read(0x81,64,timeout=1000))
    def sendCommand(self,operation, value):
        """Send a USB Control transfer.  Normally this is used to set an EEPROM value."""
        if not self.verifyReady(operation):
            self.stopSampling()
            #TODO:  We might smooth this behavior over later, but for now we want to explicitly fail if this occurs.
            raise ValueError("Power Monitor Error, attempted to send a command while the unit is in Sample Mode.")
        value = int(value)
        value_array = struct.unpack("4B",struct.pack("I",value))
        operation_array = struct.unpack("4b",struct.pack("I",operation))
        wValue = struct.unpack("H",struct.pack("BB",value_array[0],value_array[1]))[0]
        wIndex = struct.unpack("H",struct.pack("BB",operation_array[0],value_array[2]))[0]
        self.DEVICE.ctrl_transfer(op.Control_Codes.USB_OUT_PACKET,op.Control_Codes.USB_SET_VALUE,wValue,wIndex,value_array,5000)

    def stopSampling(self):
        """Send a control transfer instructing the Power Monitor to stop sampling."""
        self.verifyReady(0x02)
        self.DEVICE.ctrl_transfer(op.Control_Codes.USB_OUT_PACKET,op.Control_Codes.USB_REQUEST_STOP,0,0,0,5000)

    def startSampling(self,calTime, maxTime):
        """Instruct the Power Monitor to enter sample mode.
        calTime = Amount of time, in ms, between calibration samples.
        maxTime = Number of samples to take before exiting sample mode automatically."""
        if not self.verifyReady(0x02):
            self.stopSampling()
            raise ValueError("Power Monitor Error, attempted to start while already started.")
        value_array = struct.unpack("4B",struct.pack("I",calTime))
        maxtime_array = struct.unpack("4B",struct.pack("I",maxTime))
        wValue = struct.unpack("H",struct.pack("BB",value_array[0],value_array[1]))[0]
        wIndex = struct.unpack("H",struct.pack("BB",0,0))[0]
        self.DEVICE.ctrl_transfer(op.Control_Codes.USB_OUT_PACKET,op.Control_Codes.USB_REQUEST_START,wValue,wIndex,maxtime_array,1000)

    def resetToBootloader(self):
        wValue = 0
        wIndex = 0
        wLength = 0
        #This will cause a disconnect event, which throws an exception in libusb.
        try:
            self.DEVICE.ctrl_transfer(op.Control_Codes.USB_OUT_PACKET,op.Control_Codes.USB_REQUEST_RESET_TO_BOOTLOADER,wValue,wIndex,wLength,1000)
        except:
            print("Resetting to bootloader")

    def getValue(self,operation,valueLength, signed = False):
        """Get an EEPROM value from the Power Monitor."""
        operation_array = struct.unpack("4b",struct.pack("I",operation))
        wIndex = struct.unpack("H",struct.pack("bb",operation_array[0],0))[0]
        result = self.DEVICE.ctrl_transfer(op.Control_Codes.USB_IN_PACKET,op.Control_Codes.USB_SET_VALUE,0,wIndex,4,5000)
        if(result == op.ReturnCodes.ERROR):
            self.stopSampling()
            raise ValueError("Error code returned.  Attempted to query Power Monitor while in sample mode.")
        if(valueLength == 4):
            if(signed):
                result = struct.unpack("i",result)[0]
            else:
                result = struct.unpack("I",result)[0]
        elif(valueLength == 2):
            if(signed):
                result = struct.unpack("h",result[0:2])[0]
            else:
                result = struct.unpack("H",result[0:2])[0]
        elif(valueLength == 1):
            if(signed):
                result = struct.unpack("b",result[0:1])[0]
            else:
                result = struct.unpack("B",result[0:1])[0]
        return result

    def closeDevice(self):
        """Cleanup any loose ends, if present."""
        self.stopSampling()
        self.DEVICE.reset() #Releases the bulk endpoint, which dispose_resources apparently doesn't release.
        usb.util.dispose_resources(self.DEVICE) 


    def verifyReady(self,opcode):
        """Check whether we're currently in sample mode.
        Some commands can cause errors if we are.
        Current behavior checks for all opcodes, though there are some specific ones which will not return an error code."""

        #Only check if the firmware version is 26 or greater
        #getStartStatus command does not include 'Sample mode' bit before that revision.
        firmwareRev = self.getValue(op.OpCodes.FirmwareVersion,1)
        if(firmwareRev >= 26):
            status = self.getValue(op.OpCodes.getStartStatus, 1)
            return not np.bitwise_and(0x80,status)
        else:
            return True

class CPP_Backend_Protocol(object):
    """Uses C++ backend with libusb.
    When connecting to multiple Power Monitors with the same computer, native Python code is often too slow, and results in many dropped samples.
    This offloads the the time-critical parts of sample collection to C++, but isn't compatible with every OS yet.
    """
    def __init__(self):
        self.DEVICE = self.loadLibrary()
        self.DEVICE.pySetup.argtypes = (ctypes.c_int, ctypes.c_int,ctypes.c_int)
        self.DEVICE.pyStart.argtypes = (ctypes.c_int,ctypes.c_int)
        self.DEVICE.pyGetBulkData.argtypes = (ctypes.c_int, ctypes.POINTER(ctypes.c_uint8))
        self.DEVICE.pySendCommand.argtypes = (ctypes.c_ubyte, ctypes.c_int)
        self.DEVICE.pyGetValue.argtypes = (ctypes.c_ubyte,ctypes.c_int)
        self.queueSize = 1024
        self.Queue = (ctypes.c_uint8*self.queueSize)()
        ctypes.cast(self.Queue,ctypes.POINTER(ctypes.c_uint8))

    def Connect(self,deviceType, serialno=None):
        VID = 0x2AB9
        PID = 0x0001
        self.DEVICE.pySetup(VID,PID,serialno)
        pass

    def BulkRead(self):
        self.DEVICE.pyGetBulkData(self.queueSize,self.Queue)
        count = self.DEVICE.pyQueueCount()
        result = self.Queue[0:count*64]
        return result

    def sendCommand(self,operation, value):
        """Send a USB Control transfer.  Normally this is used to set an EEPROM value."""
        self.DEVICE.pySendCommand(operation,int(value))

    def stopSampling(self):
        """Send a control transfer instructing the Power Monitor to stop sampling."""
        self.DEVICE.pyStop()

    def startSampling(self,calTime, maxTime):
        """Instruct the Power Monitor to enter sample mode.
        calTime = Amount of time, in ms, between calibration samples.
        maxTime = Number of samples to take before exiting sample mode automatically."""
        self.DEVICE.pyStart(calTime,maxTime)


    def getValue(self,operation,valueLength):
        """Get an EEPROM value from the Power Monitor."""
        return self.DEVICE.pyGetValue(operation,valueLength)
    def closeDevice(self):
        """Cleanup any loose ends, if present."""
        self.DEVICE.pyClose();
        pass

    def loadLibrary(self):
        """Tries to load the library in an OS-neutral way."""
        #TODO:  Currently we're distributing pre-compiled .dll and .so files.
        #The proper way to do this will be including a makefile and compiling these libraries on installation.
        path = os.path.abspath(__file__)
        path = os.path.realpath(path)
        path = os.path.dirname(path)
        if(platform.system() == "Linux"):
            libLocation=os.path.join(path,"Compiled/Linux/libcpp_backend.so")
        elif(platform.system() is "Windows"):
            libLocation = os.path.join(path,"Compiled//WIN32//Cpp_backend.dll")
        else:
            raise NotImplementedError("OS not currently supported.")
        test = ctypes.CDLL(libLocation)
        return test
    def reconnect(self):
        raise NotImplementedError
    def findAllSerialNumbers(self):
        raise NotImplementedError

