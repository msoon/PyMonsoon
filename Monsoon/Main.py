import LVPM
import HVPM
import sampleEngine
import Operations as op
import HVPM

HVMON = HVPM.Monsoon()
HVMON.setup_usb()


print("HVPM Serial Number: " + repr(HVMON.getSerialNumber()))
Mon = LVPM.Monsoon()
Mon.setup_usb()
print("LVPM Serial number: " + repr(Mon.getSerialNumber()))

Mon.fillStatusPacket()
HVMON.fillStatusPacket()
Mon.setVout(4.5)
HVMON.setVout(3)
engine = sampleEngine.SampleEngine(Mon)

HVengine = sampleEngine.SampleEngine(HVMON)



HVengine.enableCSVOutput("HV Main Example.csv")
HVengine.ConsoleOutput(True)

engine.enableCSVOutput("Main Example.csv")
engine.ConsoleOutput(True)



#Test the HVPM
numSamples=sampleEngine.triggers.SAMPLECOUNT_INFINITE #Don't stop based on sample count, continue until the trigger conditions have been satisfied.
HVengine.setStartTrigger(sampleEngine.triggers.GREATER_THAN,0) #Start when we exceed 0 s
HVengine.setStopTrigger(sampleEngine.triggers.GREATER_THAN,5) #Stop when we exceed 5 s.
HVengine.setTriggerChannel(sampleEngine.channels.timeStamp) #Start and stop judged by the timestamp channel.
HVengine.startSampling(numSamples)

print("\nEnding HVPM, begin LVPM\n")

#Test the LVPM
numSamples=sampleEngine.triggers.SAMPLECOUNT_INFINITE #Don't stop based on sample count, continue until the trigger conditions have been satisfied.
engine.setStartTrigger(sampleEngine.triggers.GREATER_THAN,0) #Start when we exceed 0 s
engine.setStopTrigger(sampleEngine.triggers.GREATER_THAN,5) #Stop when we exceed 5 s.
engine.setTriggerChannel(sampleEngine.channels.timeStamp) #Start and stop judged by the timestamp channel.
engine.startSampling(numSamples)


#Diable Main channels
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
engine.ConsoleOutput(False)
engine.enableCSVOutput("All Test.csv")
engine.startSampling(5000)

#Enable every channel, take measurements, and retrieve them as a Python list.
engine.disableCSVOutput()
engine.startSampling(5000)
samples = engine.getSamples()

#Samples are stored in order, indexed sampleEngine.channels values

#for i in range(len(samples[sampleEngine.channels.timeStamp])):
#    timeStamp = samples[sampleEngine.channels.timeStamp][i]
#    Current = samples[sampleEngine.channels.MainCurrent][i]
#    print("Main current at time " + repr(timeStamp) + " is: " + repr(Current) + "mA")
