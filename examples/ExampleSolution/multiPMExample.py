import Monsoon.HVPM as HVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
import Monsoon.pmapi as pmapi
from multiprocessing import Process


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

    HVMON.closeDevice();

def main():
    serialnos = [60000]
    for serial in serialnos:
        p = Process(target=testHVPM,args=(serial,pmapi.USB_protocol()))
        p.start()

if __name__ == "__main__":
    main()