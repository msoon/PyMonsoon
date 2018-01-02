import Monsoon.HVPM as HVPM
import Monsoon.LVPM as LVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
import Monsoon.pmapi as pmapi
import numpy as np
import usb
import logging
import os
os.environ['PYUSB_DEBUG'] = 'debug'
os.environ['PYUSB_LOG_FILENAME'] = 'pyusb.log'

usb._setup_log()
#Initial commit of test cases.
#Primary concern at this point is testing fixes for the disconnect bug.
#Eventually expand other test cases so we have an automated test for every function in the library.

def testListOutput(serialno=None,Protocol=pmapi.USB_protocol()):
    """Test case 1.
    Basic connection, outputs as a Python list."""
    Mon = HVPM.Monsoon()
    Mon.setup_usb(serialno,Protocol)
    Engine = sampleEngine.SampleEngine(Mon)
    Engine.ConsoleOutput(False)
    numSamples = 5000
    Engine.startSampling(numSamples)
    samples = Engine.getSamples()

    timestamp = samples[sampleEngine.channels.timeStamp]
    mainCurrent = samples[sampleEngine.channels.MainCurrent]
    auxCurrent = samples[sampleEngine.channels.AuxCurrent]
    usbCurrent = samples[sampleEngine.channels.USBCurrent]
    mainVoltage = samples[sampleEngine.channels.MainVoltage]
    usbVoltage = samples[sampleEngine.channels.USBVoltage]

    #Do something with this information

    pass
def testCSVOutput(serialno=None,Protocol=pmapi.USB_protocol()):
    """Test case 2:
    CSV Output."""
    #Setting all channels enabled
    Mon = HVPM.Monsoon()
    Mon.setup_usb(serialno,Protocol)
    Engine = sampleEngine.SampleEngine(Mon)
    Engine.ConsoleOutput(False)
    Engine.enableChannel(sampleEngine.channels.MainCurrent)
    Engine.enableChannel(sampleEngine.channels.MainVoltage)
    Engine.enableChannel(sampleEngine.channels.USBCurrent)
    Engine.enableChannel(sampleEngine.channels.USBVoltage)
    Engine.enableChannel(sampleEngine.channels.AuxCurrent)
    Engine.enableChannel(sampleEngine.channels.timeStamp)
    Engine.enableCSVOutput("Test3.csv")
    Engine.startSampling(3000000,100) #Collect 10 minutes worth of samples a 1/100 granularity
    Mon.closeDevice()

def testDisconnectBugSevere(serialno=None,Protocol=pmapi.USB_protocol()):
    """This will force the disconnect bug to occur in a short period of time.
    This one doesn't necessarily need to pass, but an ideal fix would allow it to do so."""
    Mon = HVPM.Monsoon()
    Mon.setup_usb(serialno,Protocol)
    Engine = sampleEngine.SampleEngine(Mon)
    Engine.ConsoleOutput(False)
    i = 0
    for i in range(5000):
        i += 1
        try:
            Mon.StartSampling()
            Mon.stopSampling()
            print(i)
        except usb.core.USBError as e:
            print("Expected error hit.  Reconnecting")
            print(e.backend_error_code)
            Mon.Reconnect()
            Mon.stopSampling()

    Mon.closeDevice();

def testDisconnectBug(serialno=None,Protocol=pmapi.USB_protocol()):
    """Test for start sampling disconnect bug.
    This is the normal use case for customers who encounter the bug.
    In an ideal solution, it will pass."""
    Mon = HVPM.Monsoon()
    Mon.setup_usb(serialno,Protocol)
    Engine = sampleEngine.SampleEngine(Mon)
    Engine.ConsoleOutput(False)
    i = 0
    for i in range(5000):
        i += 1
        try:
            Engine.startSampling(10)
            print(i)
        except usb.core.USBError as e:
            print("Expected error hit.  Reconnecting")
            print(e.backend_error_code)
            Mon.Reconnect()
            Mon.stopSampling()
    Mon.closeDevice();

def testVoltageBug(serialno=None,Protocol=pmapi.USB_protocol()):
    """If a command is sent to the Power Monitor to setVout while it is in sample mode, there is a high probability the voltage will be set to a random value, and the unit will crash.
    During normal operation, this can occur if setVout is called immediately after stopSampling().  Depending on the timing, the unit might not actually be out of sample mode when the setVout command is received."""
    Mon = HVPM.Monsoon()
    Mon.setup_usb(serialno,Protocol)
    Engine = sampleEngine.SampleEngine(Mon)
    Engine.ConsoleOutput(False)
    i = 0
    reconnects = 0
    Mon.setVout(0.8)
    for i in range(5000):
        i += 1
        Engine.startSampling(50)
        Mon.setVout(0.8)
        samples = Engine.getSamples()
        voltage = np.array(samples[sampleEngine.channels.MainVoltage])
        if(np.any(voltage > 1.0)):
            #Here we're checking to see if there's a condition where it didn't fail, but the voltage is still wrong.
            #This should probably never happen, but let's be sure about that.
            print("Error, voltage is wrong")
            assert(False)
        print(i)
    Mon.closeDevice();

def main():
    testDisconnectBug()
if __name__ == "__main__":
    main()