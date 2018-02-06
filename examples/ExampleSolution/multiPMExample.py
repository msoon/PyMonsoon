import Monsoon.HVPM as HVPM
import Monsoon.LVPM as LVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
import Monsoon.pmapi as pmapi
import numpy as np
import usb

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
    for i in range(50):
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

def testVoltageBugSingle(serialno=None,Protocol=pmapi.USB_protocol()):
    """If a command is sent to the Power Monitor to setVout while it is in sample mode, there is a high probability the voltage will be set to a random value, and the unit will crash.
    During normal operation, this can occur if setVout is called immediately after stopSampling().  Depending on the timing, the unit might not actually be out of sample mode when the setVout command is received."""
    Mon = HVPM.Monsoon()
    Mon.setup_usb(serialno,Protocol)
    Engine = sampleEngine.SampleEngine(Mon)
    Engine.ConsoleOutput(False)
    i = 0
    Mon.setVout(4.2)
    for i in range(5000):
        i += 1
        try:
            Engine.startSampling(500)
            Mon.setVout(4.2)
            samples = Engine.getSamples()
            voltage = np.array(samples[sampleEngine.channels.MainVoltage])
            if(np.any(voltage > 4.4)):
                #Here we're checking to see if there's a condition where it didn't fail, but the voltage is still wrong.
                #This should probably never happen, but let's be sure about that.
                print("Error, voltage is wrong")
                assert(False)
            print(i)
        except usb.core.USBError as e:
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
    v = 0.8
    end = 4.2
    Mon.setVout(v)
    for i in range(5):
        i += 1
        v = 0.8
        try:
            Engine.startSampling(500)
            #Mon.setVout(v)
            if v < 0.8:
                v = 0.8
            while v < end:
                Mon.setVout(v)
                v += 0.3
            Mon.setVout(end)
            samples = Engine.getSamples()
            voltage = np.array(samples[sampleEngine.channels.MainVoltage])
            if(np.any(voltage > 4.4)):
                #Here we're checking to see if there's a condition where it didn't fail, but the voltage is still wrong.
                #This should probably never happen, but let's be sure about that.
                print("Error, voltage is wrong")
                assert(False)
            print(i)
        except usb.core.USBError as e:
            print(e.backend_error_code)
            Mon.Reconnect()
            Mon.stopSampling()
    Mon.closeDevice();

def main():
    #serialnos = [20488]#, 20019, 20486], 20487]
    #p2 = Process(target=testVoltageBugSingle,args=(serialnos[0],pmapi.USB_protocol()))
    #p2.start()
    #for serial in serialnos[1:3]:
    #    p = Process(target=testVoltageBug,args=(serial,pmapi.USB_protocol()))
    #    p.start()
    testDisconnectBug()
if __name__ == "__main__":
    main()