import Monsoon.HVPM as HVPM
import Monsoon.LVPM as LVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
import Monsoon.pmapi as pmapi
import numpy as np

def testHVPM(serialno=None,Protocol=pmapi.USB_protocol()):
    HVMON = HVPM.Monsoon()
    HVMON.setup_usb(serialno,Protocol)
    print("HVPM Serial Number: " + repr(HVMON.getSerialNumber()))
    HVMON.fillStatusPacket()
    HVMON.setVout(3)
    HVengine = sampleEngine.SampleEngine(HVMON)
    #Output to CSV
    HVengine.enableCSVOutput("HV Main Example.csv")
    #Turning off periodic console outputs.
    HVengine.ConsoleOutput(True)

    #Setting all channels enabled
    HVengine.enableChannel(sampleEngine.channels.MainCurrent)
    HVengine.enableChannel(sampleEngine.channels.MainVoltage)
    HVengine.enableChannel(sampleEngine.channels.USBCurrent)
    HVengine.enableChannel(sampleEngine.channels.USBVoltage)
    HVengine.enableChannel(sampleEngine.channels.AuxCurrent)
    HVengine.enableChannel(sampleEngine.channels.timeStamp)
    
    #Setting trigger conditions
    numSamples=sampleEngine.triggers.SAMPLECOUNT_INFINITE 
    HVengine.setStartTrigger(sampleEngine.triggers.GREATER_THAN,0) 
    HVengine.setStopTrigger(sampleEngine.triggers.GREATER_THAN,5) 
    HVengine.setTriggerChannel(sampleEngine.channels.timeStamp) 

    #Actually start collecting samples
    HVengine.startSampling(numSamples)
    #startSampling() continues until the trigger conditions have been met, and then ends automatically.
    #Measurements are automatically saved to the filename passed in enableCSVOutput()

    #Disable CSV Output
    HVengine.disableCSVOutput()
    #Collect another 5 seconds worth of samples
    HVengine.startSampling(numSamples)
    #Get those samples as a Python list
    samples = HVengine.getSamples()
    #Samples has the format  [[timestamp], [mainCurrent], [usbCurrent], [auxCurrent], [mainVolts],[usbVolts]]
    #Use sampleEngine.channel to select the appropriate list index.
    timestamp = samples[sampleEngine.channels.timeStamp]
    mainCurrent = samples[sampleEngine.channels.MainCurrent]
    auxCurrent = samples[sampleEngine.channels.AuxCurrent]
    usbCurrent = samples[sampleEngine.channels.USBCurrent]
    mainVoltage = samples[sampleEngine.channels.MainVoltage]
    usbVoltage = samples[sampleEngine.channels.USBVoltage]

    #Perform analysis on the resulting data.  For example, in order to calculate, perform the following:
    #mainCurrent is given in mA.  Divide by 1000 to convert to Amps
    scaledMainCurrent = [x / 1000 for x in mainCurrent]
    #Element-wise multiply to produce Watts. Power = Current * Voltage.  
    mainPower = np.multiply(scaledMainCurrent, mainVoltage) 

    #When finished, close the device.
    HVMON.closeDevice();

def testLVPM(serialno=None,Protcol=pmapi.USB_protocol()):
    Mon = LVPM.Monsoon()
    Mon.setup_usb(serialno,Protcol)
    print("LVPM Serial number: " + repr(Mon.getSerialNumber()))
    Mon.fillStatusPacket()
    Mon.setVout(4.5)
    engine = sampleEngine.SampleEngine(Mon)
    engine.enableCSVOutput("Main Example.csv")
    engine.ConsoleOutput(True)
    #test main channels
    numSamples=sampleEngine.triggers.SAMPLECOUNT_INFINITE #Don't stop based on sample count, continue until the trigger conditions have been satisfied.
    engine.setStartTrigger(sampleEngine.triggers.GREATER_THAN,0) #Start when we exceed 0 s
    engine.setStopTrigger(sampleEngine.triggers.GREATER_THAN,5) #Stop when we exceed 5 s.
    engine.setTriggerChannel(sampleEngine.channels.timeStamp) #Start and stop judged by the timestamp channel.
    engine.startSampling(numSamples)


    #Disable Main channels
    engine.disableChannel(sampleEngine.channels.MainCurrent)
    engine.disableChannel(sampleEngine.channels.MainVoltage)

    engine.setStartTrigger(sampleEngine.triggers.GREATER_THAN,5)
    engine.setStopTrigger(sampleEngine.triggers.GREATER_THAN,10)
    engine.setTriggerChannel(sampleEngine.channels.timeStamp)
    #Take measurements from the USB Channel
    Mon.setVout(0)
    #Set USB Passthrough mode to 'on,' since it defaults to 'auto' and will turn off when sampling mode begins.
    Mon.setUSBPassthroughMode(op.USB_Passthrough.On)
    #Enable USB channels
    engine.enableChannel(sampleEngine.channels.USBCurrent)
    engine.enableChannel(sampleEngine.channels.USBVoltage)
    engine.enableCSVOutput("USB Test.csv")
    engine.startSampling(5000)

    #Enable every channel, take measurements
    engine.enableChannel(sampleEngine.channels.MainVoltage)
    engine.enableChannel(sampleEngine.channels.MainCurrent)
    #Enable Aux channel
    engine.enableChannel(sampleEngine.channels.AuxCurrent)
    Mon.setVout(2.5)
    engine.enableCSVOutput("All Test.csv")
    engine.startSampling(5000)

    #Enable every channel, take measurements, and retrieve them as a Python list.
    engine.disableCSVOutput()
    engine.startSampling(5000)
    samples = engine.getSamples()
    Mon.closeDevice();

def main():
    LVPMSerialNo = 60001
    HVPMSerialNo = 60000
    testLVPM(LVPMSerialNo,pmapi.USB_protocol())
    testHVPM(HVPMSerialNo,pmapi.USB_protocol())

if __name__ == "__main__":
    main()