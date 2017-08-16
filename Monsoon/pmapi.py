import struct
import Operations as op

class USB_protocol(object):
    """Currently the only officially supported protocol."""
    def __init__(self, device):
        self.DEVICE = device
    

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
        self.DEVICE.ctrl_transfer(op.Control_Codes.USB_IN_PACKET,op.Control_Codes.USB_REQUEST_STOP,0,0,0,5000)

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
    