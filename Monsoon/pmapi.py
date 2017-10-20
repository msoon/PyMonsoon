import struct
import Operations as op
import ctypes
import platform
import usb.core
import usb.util
import numpy as np


class USB_protocol(object):
    """Currently the only officially supported protocol."""
    def __init__(self):
        self.DEVICE = None

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
        return(self.DEVICE.read(0x81,64,timeout=0))
    def sendCommand(self,operation, value):
        """Send a USB Control transfer.  Normally this is used to set an EEPROM value."""
        try:
            value = int(value)
            value_array = struct.unpack("4b",struct.pack("I",value))
            operation_array = struct.unpack("4b",struct.pack("I",operation))
            wValue = struct.unpack("H",struct.pack("bb",value_array[0],value_array[1]))[0]
            wIndex = struct.unpack("H",struct.pack("bb",operation_array[0],value_array[2]))[0]
            self.DEVICE.ctrl_transfer(op.Control_Codes.USB_OUT_PACKET,op.Control_Codes.USB_SET_VALUE,wValue,wIndex,"0",5000)
        except:
            print("Control Transfer Error")

    def stopSampling(self):
        """Send a control transfer instructing the Power Monitor to stop sampling."""
        self.DEVICE.ctrl_transfer(op.Control_Codes.USB_OUT_PACKET,op.Control_Codes.USB_REQUEST_STOP,0,0,0,5000)

    def startSampling(self,calTime, maxTime):
        """Instruct the Power Monitor to enter sample mode.  
        calTime = Amount of time, in ms, between calibration samples.
        maxTime = Number of samples to take before exiting sample mode automatically."""
        value_array = struct.unpack("4B",struct.pack("I",calTime))
        maxtime_array = struct.unpack("4B",struct.pack("I",maxTime))
        wValue = struct.unpack("H",struct.pack("BB",value_array[0],value_array[1]))[0]
        wIndex = struct.unpack("H",struct.pack("BB",op.Control_Codes.USB_REQUEST_START,0))[0]
        self.DEVICE.ctrl_transfer(op.Control_Codes.USB_OUT_PACKET,op.Control_Codes.USB_REQUEST_START,wValue,wIndex,maxtime_array,1000)

    def getValue(self,operation,valueLength):
        """Get an EEPROM value from the Power Monitor."""
        operation_array = struct.unpack("4b",struct.pack("I",operation))
        wIndex = struct.unpack("H",struct.pack("bb",operation_array[0],0))[0]
        result = self.DEVICE.ctrl_transfer(op.Control_Codes.USB_IN_PACKET,op.Control_Codes.USB_SET_VALUE,0,wIndex,4,5000)
        result = struct.unpack("I",result)[0]
        return result

    def closeDevice(self):
        """Cleanup any loose ends, if present."""
        usb.util.dispose_resources(self.DEVICE)
        pass

class CPP_Backend_Protocol(object):
    """Uses C++ driver to collect bulk samples.
    Currently considered experimental.
    This sometimes results in slower processing, but guarantees fewer dropped samples
    If used, we recommend"""
    def __init__(self):

        self.DEVICE = ctypes.CDLL("Win32_Backend\Cpp_backend.dll")
        self.DEVICE.pySetup.argtypes = (ctypes.c_int, ctypes.c_int,ctypes.c_int)
        self.DEVICE.pyStart.argtypes = (ctypes.c_int,ctypes.c_int)
        self.DEVICE.pyGetBulkData.argtypes = (ctypes.c_int, ctypes.POINTER(ctypes.c_uint8))
        self.DEVICE.pySendCommand.argtypes = (ctypes.c_ubyte, ctypes.c_int)
        self.DEVICE.pyGetValue.argtypes = (ctypes.c_ubyte,ctypes.c_int)
        self.queueSize = 1024
        self.Queue = [0 for x in range(self.queueSize)]
        self.array_type = ctypes.c_uint8 * self.queueSize

    def Connect(self,deviceType, serialno=None):
        VID = 0x2AB9
        PID = 0x0001
        self.DEVICE.pySetup(VID,PID,serialno)
        pass

    def BulkRead(self):
        array_pointer = ctypes.cast(self.DEVICE.pyGetBulkData(self.queueSize,self.array_type(*self.Queue)),ctypes.POINTER(self.array_type))
        packets = np.array(array_pointer.contents)
        count = self.DEVICE.pyQueueCount()
        result = packets[0:count*64]
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