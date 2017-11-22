import Monsoon.HVPM as HVPM
import Monsoon.LVPM as LVPM
import Monsoon.sampleEngine as sampleEngine
import Monsoon.Operations as op
import Monsoon.pmapi as pmapi
import time

"""simpleSamplingExample assumes you wish to collect samples in a single bulk collection, and blocks
Processing until complete.  This shows an alternative, manually collecting small numbers of samples
at regular intervals."""

def main():
    HVMON = HVPM.Monsoon()
    HVMON.setup_usb()
    print("HVPM Serial Number: " + repr(HVMON.getSerialNumber()))
    HVMON.fillStatusPacket()
    HVMON.setVout(3)
    HVengine = sampleEngine.SampleEngine(HVMON)
    HVengine.ConsoleOutput(False)
    #Puts the Power monitor in sample mode, and starts collecting samples automatically.
    HVengine.periodicStartSampling()
    for i in range(5):
        #Collect the most recent 100 samples
        samples = HVengine.periodicCollectSamples(100) 
        print("iteration " + repr(i) + " samples collected " + repr(len(samples[0])))
        time.sleep(1) 
    #In order to change parameters like voltage and USB passthrough mode, the unit needs to exit sample mode.
    HVMON.stopSampling()
    HVMON.setVout(4.5)
    #Restart tests after changing.
    HVengine.periodicStartSampling()
    for i in range(5):
        samples = HVengine.periodicCollectSamples(100) 
        print("iteration " + repr(i) + " samples collected " + repr(len(samples[0])))
        time.sleep(1) 

    #When testing is concluded, stop sampling, turn off voltage, and close the device.
    HVMON.stopSampling()
    HVMON.setVout(0)
    HVMON.closeDevice()

if __name__ == "__main__":
    main()