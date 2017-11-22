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

    #Standard setup
    HVMON = HVPM.Monsoon()
    HVMON.setup_usb()
    print("HVPM Serial Number: " + repr(HVMON.getSerialNumber()))
    HVMON.fillStatusPacket()
    HVMON.setVout(2.5)
    HVengine = sampleEngine.SampleEngine(HVMON)
    HVengine.ConsoleOutput(False)
    #Puts the Power monitor in sample mode, and starts collecting samples automatically.
    HVengine.periodicStartSampling()
    for i in range(5):
        #Collect the most recent 100 samples
        samples = HVengine.periodicCollectSamples(100) 
        #samples has the same format as returned by getSamples(): [[timestamp], [mainCurrent], [usbCurrent], [auxCurrent], [mainVolts],[usbVolts]]
        print("iteration " + repr(i) + " samples collected " + repr(len(samples[0])))
        time.sleep(1) #Represents doing something else for a bit.

    #In order to change parameters like voltage and USB passthrough mode, the unit needs to exit sample mode.
    HVengine.periodicStopSampling()
    HVMON.setVout(4.0)
    #Use CSV output
    HVengine.enableCSVOutput("periodicExample.csv")
    #Restart tests after changing.
    HVengine.periodicStartSampling()
    for i in range(5):
        #CSV output consumes samples, so we can't use them as a python list.
        #Samples are automatically appended to the end of the csv file
        HVengine.periodicCollectSamples(100) 
        print("CSV out, iteration " + repr(i))
        time.sleep(1) 

    #When testing is concluded, stop sampling, turn off voltage, and close the device.
    HVengine.periodicStopSampling(closeCSV=True)
    HVMON.setVout(0)
    HVMON.closeDevice()

if __name__ == "__main__":
    main()