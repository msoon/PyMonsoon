import Monsoon.LVPM as LVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op

Mon = LVPM.Monsoon()
Mon.setup_usb()


Mon.setVout(4.0)
engine = sampleEngine.SampleEngine(Mon)
engine.enableCSVOutput("Main Example.csv")
engine.ConsoleOutput(True)
numSamples=50000 #sample for one second
engine.startSampling(numSamples)
#Diable Main channels
engine.disableChannel(sampleEngine.channels.MainCurrent)
engine.disableChannel(sampleEngine.channels.MainVoltage)

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
for i in range(len(samples[sampleEngine.channels.timeStamp])):
    timeStamp = samples[sampleEngine.channels.timeStamp][i]
    Current = samples[sampleEngine.channels.MainCurrent][i]
    print("Main current at time " + repr(timeStamp) + " is: " + repr(Current) + "mA")
