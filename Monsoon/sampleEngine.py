#!/usr/bin/python

import threading
import time
from Monsoon import HVPM
import struct
import time
import math
from Monsoon.calibrationData import calibrationData
from Monsoon import Operations as ops
from copy import deepcopy
import numpy as np
import signal
import sys
import usb
import os
import scipy as sp
import scipy.stats

class channels:
    timeStamp = 0
    MainCurrent = 1
    USBCurrent = 2
    AuxCurrent = 3
    MainVoltage = 4
    USBVoltage = 5

class triggers:

    SAMPLECOUNT_INFINITE = 0xFFFFFFFF
    @staticmethod
    def GREATER_THAN(x,y):
        if(x > y):
            return True
        else:
            return False
    @staticmethod
    def LESS_THAN(x,y):
        if(x < y):
            return True
        else:
            return False
class ErrorHandlingModes:
    off = 0 #No error checking.  Use if you're seeing a large number of dropped samples
    full = 1 #Automatically handle errors
    debug = 2 #Handle errors + output logging data.  Not fully implemented yet.

class SampleEngine:
    def __init__(self, Monsoon,bulkProcessRate=128, errorMode = ErrorHandlingModes.full, calsToKeep=5):
        """Declares global variables.
        During testing, we found the garbage collector would slow down sampling enough to cause a
        lot of dropped samples.
        We've tried to combat this by allocating as much as possible in advance."""
        self.monsoon = Monsoon
        self.__errorMode = errorMode
        if(errorMode == ErrorHandlingModes.debug):
            os.environ['PYUSB_DEBUG'] = 'debug'
            os.environ['PYUSB_LOG_FILENAME'] = 'pyusb.log'
            usb._setup_log()
        self.__mainCal = calibrationData(calsToKeep)
        self.__usbCal = calibrationData(calsToKeep)
        self.__auxCal = calibrationData(calsToKeep)
        self.__padding = np.zeros((64))
        self.__fineThreshold = Monsoon.fineThreshold
        self.__auxFineThreshold = Monsoon.auxFineThreshold
        self.__ADCRatio = (float)(62.5 / 1e6); #Each tick of the ADC represents this much voltage
        self.__mainVoltageScale = Monsoon.mainvoltageScale
        self.__usbVoltageScale = Monsoon.usbVoltageScale
        self.dropped = 0
        self.bulkProcessRate = bulkProcessRate 
        self.__packetSize = 64
        self.__startTime = time.time()
        #Indices
        self.__mainCoarseIndex = 0
        self.__mainFineIndex = 1
        self.__usbCoarseIndex = 2
        self.__usbFineIndex = 3
        self.__auxCoarseIndex = 4
        self.__auxFineIndex = 5
        self.__mainVoltageIndex = 6
        self.__usbVoltageIndex = 7
        self.__timestampIndex = 10

        #Output lists
        self.__mainCurrent = []
        self.__usbCurrent = []
        self.__auxCurrent = []
        self.__usbVoltage = []
        self.__mainVoltage = []
        self.__timeStamps = []

        #Output controls
        self.__outputConsoleMeasurements = True
        self.__outputTimeStamp = True
        self.__collectMainMeasurements = True
        self.__collectUSBMeasurements = False
        self.__collectAuxMeasurements = False
        self.__collectMainVoltage = True
        self.__collectUSBVoltage = False
        self.__channels = [self.__outputTimeStamp, self.__collectMainMeasurements,self.__collectUSBMeasurements,self.__collectAuxMeasurements,self.__collectMainVoltage,self.__collectUSBVoltage]
        self.__channelnames = ["Time(ms)","Main(mA)", "USB(mA)", "Aux(mA)", "Main Voltage(V)", "USB Voltage(V)"]
        self.__channelOutputs = [self.__mainCurrent,self.__usbCurrent,self.__auxCurrent,self.__mainVoltage,self.__usbVoltage]
        self.__sampleCount = 0
        self.__CSVOutEnable = False

        #Trigger Settings
        self.__startTriggerSet = False
        self.__stopTriggerSet = False
        self.__triggerChannel = channels.timeStamp
        self.__startTriggerLevel = 0
        self.__startTriggerStyle = np.vectorize(triggers.GREATER_THAN)
        self.__stopTriggerLevel = triggers.SAMPLECOUNT_INFINITE
        self.__stopTriggerStyle = np.vectorize(triggers.GREATER_THAN)
        self.__sampleLimit = 50000

        #output writer
        self.__f = None

        pass

    def setStartTrigger(self,triggerStyle,triggerLevel):
        """Controls the conditions when the sampleEngine starts recording measurements."""
        """triggerLevel: threshold for trigger start."""
        """triggerStyle:  GreaterThan or Lessthan."""
        self.__startTriggerLevel = triggerLevel
        self.__startTriggerStyle = np.vectorize(triggerStyle)
        pass

    def setStopTrigger(self,triggerstyle,triggerlevel):
        """Controls the conditions when the sampleEngine stops recording measurements."""
        """triggerLevel: threshold for trigger stop."""
        """triggerStyle:  GreaterThan or Lessthan."""
        self.__stopTriggerLevel = triggerlevel
        self.__stopTriggerStyle = np.vectorize(triggerstyle)

    def setTriggerChannel(self, triggerChannel):
        """Sets channel that controls the trigger.
        triggerChannel:  selected from sampleEngine.channels"""
        
        self.__triggerChannel = triggerChannel

    def ConsoleOutput(self, boolValue):
        """Enables or disables the display of realtime measurements
        boolValue:  True == Enable, False == Disable"""
        self.__outputConsoleMeasurements = boolValue

    def enableChannel(self,channel):
        """Enables a channel.  Takes sampleEngine.channel class value as input.
        channel: selected from sampleEngine.channels"""
        self.__channels[channel] = True


    def disableChannel(self,channel):
        """Disables a channel.  Takes sampleEngine.channel class value as input.
        channel: selected from sampleEngine.channels"""
        self.__channels[channel] = False

    def enableCSVOutput(self, filename):
        """Opens a file and causes the sampleEngine to periodically output samples when taking
        measurements
        filename: The file measurements will be output to."""
        self.__outputFilename = filename
        self.__f = open(filename,"w")
        self.__CSVOutEnable = True

    def disableCSVOutput(self):
        """Closes the CSV file if open and disables CSV output."""
        if(self.__f is not None):
            self.__f.close()
            self.__f = None
        self.__CSVOutEnable = False
    def __Reset(self):
        self.__startTriggerSet = False
        self.__stopTriggerSet = False;
        self.__sampleCount = 0
        self.__mainCal.clear()
        self.__usbCal.clear()
        self.__auxCal.clear()

        self.__ClearOutput()

    def __ClearOutput(self):
        """Wipes away all of the old output data."""
        self.__mainCurrent = []
        self.__usbCurrent = []
        self.__auxCurrent = []
        self.__usbVoltage = []
        self.__mainVoltage = []
        self.__timeStamps = []

    def __isCalibrated(self):
        """Returns true if every channel has sufficient calibration samples."""
        A = self.__mainCal.calibrated()
        B = self.__usbCal.calibrated()
        C = self.__auxCal.calibrated()
        return A and B and C

    def __addMeasurement(self,channel,measurement):
        """Adds measurements to the global list of measurements.
        channel: selected from sampleEngine.channels
        measurement:  An 1xn array of measurements.
        """
        if(channel == self.__triggerChannel and not self.__startTriggerSet):
            self.__evalStartTrigger(measurement)
        elif(channel == self.__triggerChannel):
            self.__evalStopTrigger(measurement[::self.__granularity])

        measurements = self.__getMeasurement(measurement)
        if(channel == channels.MainCurrent and not self.__stopTriggerSet):
            self.__mainCurrent.append(measurements)

        if(channel == channels.USBCurrent):
            self.__usbCurrent.append(measurements)
        if(channel == channels.AuxCurrent):
            self.__auxCurrent.append(measurements)
        if(channel == channels.USBVoltage):
            self.__usbVoltage.append(measurements)
        if(channel == channels.MainVoltage):
            self.__mainVoltage.append(measurements)
        if(channel == channels.timeStamp):
            self.__timeStamps.append(measurements)
            self.__sampleCount += len(measurements)

    def __getMeasurement(self, measurement):
        measurements = []
        if ((self.__sampleCount + len(measurement[::self.__granularity])) > self.__sampleLimit):
            counter = self.__sampleCount
            for sample in measurement[::self.__granularity]:
                if (counter >= self.__sampleLimit):
                    break
                measurements.append(sample)
                counter += 1
        else:
            measurements = measurement
        return measurements

    def __evalStartTrigger(self, measurement):
        """
        See if any of the measurements meet the conditions to start recording samples.
        measurement:  a 1xn array.
        """
        self.__startTriggerStyle(measurement,self.__startTriggerLevel)
        self.__startTriggerSet = np.any(self.__startTriggerStyle(measurement,self.__startTriggerLevel))

    def __evalStopTrigger(self,measurement):
        """
        See if any of the measurements meet the conditions to stop recording samples.
        measurement:  a 1xn array of measurements.
        """
        if(self.__sampleCount >= self.__sampleLimit and self.__sampleLimit is not triggers.SAMPLECOUNT_INFINITE):
            self.__stopTriggerSet = True
        if(self.__stopTriggerLevel is not triggers.SAMPLECOUNT_INFINITE):
            test = self.__stopTriggerStyle(measurement,self.__stopTriggerLevel)
            if(np.any(test)):
                self.__stopTriggerSet = True

    def __vectorProcess(self,measurements):
        """Translates raw ADC measurements into current values.
        measurements:  An nxm array of integers indexed by the global channel index scheme.
        """
        #Currents
        if(self.__isCalibrated()):
            measurements = np.array(measurements)
            sDebug = ""
            if(self.__channels[channels.MainCurrent]):
            #Main Coarse
                scale = self.monsoon.statusPacket.mainCoarseScale
                zeroOffset = self.monsoon.statusPacket.mainCoarseZeroOffset
                calRef = self.__mainCal.getRefCal(True)
                calZero = self.__mainCal.getZeroCal(True)
                zeroOffset += calZero
                if(calRef - zeroOffset != 0):
                    slope = scale / (calRef - zeroOffset)
                else:
                    slope = 0
                Raw = measurements[:,self.__mainCoarseIndex] - zeroOffset
                mainCoarseCurrents = Raw * slope

                #Main Fine
                scale = self.monsoon.statusPacket.mainFineScale
                zeroOffset = self.monsoon.statusPacket.mainFineZeroOffset
                calRef = self.__mainCal.getRefCal(False)
                calZero = self.__mainCal.getZeroCal(False)
                zeroOffset += calZero
                if(calRef - zeroOffset != 0):
                    slope = scale / (calRef - zeroOffset)
                else:
                    slope = 0
                Raw = measurements[:,self.__mainFineIndex] - zeroOffset
                mainFinecurrents = Raw * slope / 1000
                mainCurrent = np.where(measurements[:,self.__mainFineIndex] < self.__fineThreshold, mainFinecurrents, mainCoarseCurrents)
                self.__addMeasurement(channels.MainCurrent,mainCurrent)
                #self.__mainCurrent.append(mainCurrent)
                sDebug = "Main Current: " + repr(round(mainCurrent[0],2))

            if(self.__channels[channels.USBCurrent]):
                #USB Coarse
                scale = self.monsoon.statusPacket.usbCoarseScale
                zeroOffset = self.monsoon.statusPacket.usbCoarseZeroOffset
                calRef = self.__usbCal.getRefCal(True)
                calZero = self.__usbCal.getZeroCal(True)
                zeroOffset += calZero
                if(calRef - zeroOffset != 0):
                    slope = scale / (calRef - zeroOffset)
                else:
                    slope = 0
                Raw = measurements[:,self.__usbCoarseIndex] - zeroOffset
                usbCoarseCurrents = Raw * slope

                #USB Fine
                scale = self.monsoon.statusPacket.usbFineScale
                zeroOffset = self.monsoon.statusPacket.usbFineZeroOffset
                calRef = self.__usbCal.getRefCal(False)
                calZero = self.__usbCal.getZeroCal(False)
                zeroOffset += calZero
                if(calRef - zeroOffset != 0):
                    slope = scale / (calRef - zeroOffset)
                else:
                    slope = 0
                Raw = measurements[:,self.__usbFineIndex] - zeroOffset
                usbFineCurrents = Raw * slope/ 1000
                usbCurrent = np.where(measurements[:,self.__usbFineIndex] < self.__fineThreshold, usbFineCurrents, usbCoarseCurrents)
                self.__addMeasurement(channels.USBCurrent,usbCurrent)
                #self.__usbCurrent.append(usbCurrent)
                sDebug = sDebug + " USB Current: " + repr(round(usbCurrent[0], 2))

            if(self.__channels[channels.AuxCurrent]):
                #Aux Coarse
                scale = self.monsoon.statusPacket.auxCoarseScale
                zeroOffset = 0
                calRef = self.__auxCal.getRefCal(True)
                calZero = self.__auxCal.getZeroCal(True)
                zeroOffset += calZero
                if(calRef - zeroOffset != 0):
                    slope = scale / (calRef - zeroOffset)
                else:
                    slope = 0
                Raw = measurements[:,self.__auxCoarseIndex] - zeroOffset
                auxCoarseCurrents = Raw * slope

                #Aux Fine
                scale = self.monsoon.statusPacket.auxFineScale
                zeroOffset = 0
                calRef = self.__auxCal.getRefCal(False)
                calZero = self.__auxCal.getZeroCal(False)
                zeroOffset += calZero
                if(calRef - zeroOffset != 0):
                    slope = scale / (calRef - zeroOffset)
                else:
                    slope = 0
                Raw = measurements[:,self.__auxFineIndex] - zeroOffset
                auxFineCurrents = Raw * slope / 1000
                auxCurrent = np.where(measurements[:,self.__auxFineIndex] < self.__auxFineThreshold, auxFineCurrents, auxCoarseCurrents)
                self.__addMeasurement(channels.AuxCurrent,auxCurrent)
                #self.__auxCurrent.append(auxCurrent)
                sDebug = sDebug + " Aux Current: " + repr(round(auxCurrent[0], 2))

            #Voltages
            if(self.__channels[channels.MainVoltage]):
                mainVoltages = measurements[:,self.__mainVoltageIndex] * self.__ADCRatio * self.__mainVoltageScale
                self.__addMeasurement(channels.MainVoltage,mainVoltages)
                #self.__mainVoltage.append(mainVoltages)

                sDebug = sDebug + " Main Voltage: " + repr(round(mainVoltages[0],2))


            if(self.__channels[channels.USBVoltage]):
                usbVoltages = measurements[:,self.__usbVoltageIndex] * self.__ADCRatio * self.__usbVoltageScale
                self.__addMeasurement(channels.USBVoltage,usbVoltages)
                #self.__usbVoltage.append(usbVoltages)
                sDebug = sDebug + " USB Voltage: " + repr(round(usbVoltages[0],2))
            timeStamp = measurements[:,self.__timestampIndex]
            self.__addMeasurement(channels.timeStamp,timeStamp)
            #self.__timeStamps.append(timeStamp)
            sDebug = sDebug + " Dropped: " + repr(self.dropped)
            sDebug = sDebug + " Total Sample Count: " + repr(self.__sampleCount)
            if(self.__outputConsoleMeasurements):
                print(sDebug)
            if not self.__startTriggerSet:
                self.__ClearOutput()


    def __processPacket(self, measurements):
        """Separates received packets into ZeroCal, RefCal, and measurement samples.
        measurements:  an nxm array of swizzled packets from the Power Monitor """
        Samples = []
        for measurement in measurements:
            self.dropped = measurement[0]
            flags = measurement[1]
            numObs = measurement[2]
            offset = 3
            for _ in range(0,numObs):
                sample = measurement[offset:offset+10]
                sample.append(measurement[len(measurement)-1])
                sampletype = sample[8] & 0x30
                if(sampletype == ops.SampleType.ZeroCal):
                    self.__processZeroCal(sample)
                elif(sampletype == ops.SampleType.refCal):
                    self.__processRefCal(sample)
                elif(sampletype == ops.SampleType.Measurement):
                    Samples.append(sample)

                offset += 10
        return Samples

    def __startupCheck(self,verbose=False):
        """Verify the sample engine is setup to start."""
        if(verbose):
            print("Verifying ready to start up")
            print("Calibrating...")
        Samples = [[0 for _ in range(self.__packetSize+1)] for _ in range(self.bulkProcessRate)]
        while(not self.__isCalibrated() and self.__sampleCount < 20000):
            self.__sampleLoop(0,Samples,1)
        self.getSamples()
        if not self.__isCalibrated():
            print("Connection error, failed to calibrate after 20,000 samples")
            return False
        if not self.__channels[self.__triggerChannel]:
            print("Error:  Trigger channel not enabled.")
            return False
        return True

    def __processZeroCal(self,meas):
        """Adds raw measurement data to the zeroCal tracker
        meas:  Zerocal measurements indexed by the global channel index scheme.
        """
        self.__mainCal.addZeroCal(meas[self.__mainCoarseIndex], True)
        self.__mainCal.addZeroCal(meas[self.__mainFineIndex], False)
        self.__usbCal.addZeroCal(meas[self.__usbCoarseIndex], True)
        self.__usbCal.addZeroCal(meas[self.__usbFineIndex], False)
        self.__auxCal.addZeroCal(meas[self.__auxCoarseIndex], True)
        self.__auxCal.addZeroCal(meas[self.__auxFineIndex], False)
        return True
    def __processRefCal(self, meas):
        """Adds raw measurement data to the refcal tracker        
        meas:  RefCal measurements indexed by the global channel index scheme.
        """
        self.__mainCal.addRefCal(meas[self.__mainCoarseIndex], True)
        self.__mainCal.addRefCal(meas[self.__mainFineIndex], False)
        self.__usbCal.addRefCal(meas[self.__usbCoarseIndex], True)
        self.__usbCal.addRefCal(meas[self.__usbFineIndex], False)
        self.__auxCal.addRefCal(meas[self.__auxCoarseIndex], True)
        self.__auxCal.addRefCal(meas[self.__auxFineIndex], False)
        return True

    def getSamples(self):
        """Returns samples in a Python list.  Format is: 
        [timestamp, main, usb, aux,mainVolts,usbVolts]."""
        result = self.__arrangeSamples(True)
        return result

    def __outputToCSV(self):
        """This is intended to be called periodically during sampling.
        The alternative is to store measurements in an array or queue, which will overflow allocated
        memory within a few hours depending on system settings.
        Writes measurements to a CSV file"""

        output = self.__arrangeSamples()
        for i in range(len(output[0])):
            sOut = ""
            for j in range(len(output)):
                sOut = sOut + repr(output[j][i]) + ","
            sOut = sOut + "\n"
            self.__f.write(sOut)

    def __arrangeSamples(self, exportAllIndices = False):
        """Arranges output lists so they're a bit easier to process.
        exportAllIndices:  Populates the list with every channel, even if no measurements are stored for that channel.
        Useful for making sure the indices in sampleEngine.channels match the output from this function."""
        output = []
        times = []
        for data in self.__timeStamps:
            for measurement in data:
                times.append(measurement)
        output.append(times)
        self.__timeStamps = []
        if(self.__channels[channels.MainCurrent] or exportAllIndices):
            main = []
            for data in self.__mainCurrent:
                for measurement in data:
                    main.append(measurement)
            output.append(main)
            self.__mainCurrent = []
        if(self.__channels[channels.USBCurrent]or exportAllIndices):
            usb = []
            for data in self.__usbCurrent:
                for measurement in data:
                    usb.append(measurement)
            output.append(usb)
            self.__usbCurrent = []
        if(self.__channels[channels.AuxCurrent]or exportAllIndices):
            Aux = []
            for data in self.__auxCurrent:
                for measurement in data:
                    Aux.append(measurement)
            output.append(Aux)
            self.__auxCurrent = []
        if(self.__channels[channels.MainVoltage]or exportAllIndices):
            volts = []
            for data in self.__mainVoltage:
                for measurement in data:
                    volts.append(measurement)
            output.append(volts)
            self.__mainVoltage = []
        if(self.__channels[channels.USBVoltage]or exportAllIndices):
            volts = []
            for data in self.__usbVoltage:
                for measurement in data:
                    volts.append(measurement)
            output.append(volts)
            self.__usbVoltage = []
        return output
    def outputCSVHeaders(self):
        """Creates column headers in the CSV output file for each enabled channel."""
        for i in range(len(self.__channelnames)):
            if(self.__channels[i]):
                self.__f.write((self.__channelnames[i] + ","))
        self.__f.write("\n")

    def __sampleLoop(self, S, Samples, ProcessRate, legacy_timestamp=False):
        """
        Collects and processes samples in batches.  Numpy makes processing large numbers of samples in batches
        much faster than processing them as they're received.  Useful in avoiding dropped samples.  
        S: The number of samples in the current batch.
        Samples: An array that will be populated with samples.
        ProcessRate: Number of samples per batch.  Should be a power of 2 for best results.
        legacy_timestamp:  if true, use time.time() for timestamp instead of currentTime - startTime
        """
        buffer = self.monsoon.BulkRead()
        for start in range(0,len(buffer),64):
            if (self.__stopTriggerSet):
                break
            buf = buffer[start:start+64]
            Sample = self.monsoon.swizzlePacket(buf)
            numSamples = Sample[2]
            if (legacy_timestamp):
                Sample.append(int(time.time()))
            else:
                Sample.append(time.time() - self.__startTime)
            Samples[S] = Sample
            S += numSamples
            if(S >= ProcessRate):
                bulkPackets = self.__processPacket(Samples)
                if(len(bulkPackets) > 0):
                    self.__vectorProcess(bulkPackets)
                S = 0
        return S

    def __startSampling(self, samples=5000, granularity=1, legacy_timestamp=False, calTime = 1250, output_callback=None):
        """Handle setup for sample collection.
        samples:  Number of samples to collect, independent of the stop trigger.  sampleEngine.triggers.SAMPLECOUNT_INFINITE to function solely through triggers.
        granularity:  Samples to store.  1 = 1:1, 10 = store 1 out of every 10 samples, etc.  
        legacy_timestamp: if true, use time.time() for timestamp instead of currentTime - startTime
        """
        self.__Reset()
        self.__granularity = granularity
        self.__sampleLimit = samples
        Samples = [[0 for _ in range(self.__packetSize+1)] for _ in range(self.bulkProcessRate)]
        S = 0
        debugcount = 0
        minutes = 0
        granularity_index = 0
        csvOutRateLimit = True
        csvOutThreshold = self.bulkProcessRate/2
        self.__startTime = time.time()
        if(self.__CSVOutEnable):
            self.outputCSVHeaders()
        self.monsoon.StartSampling(calTime,triggers.SAMPLECOUNT_INFINITE)
        if not self.__startupCheck(False):
            self.monsoon.stopSampling()
            return False
        while not self.__stopTriggerSet:
            S = self.__sampleLoop(S,Samples,self.bulkProcessRate,legacy_timestamp)
            if(S == 0):
                csvOutRateLimit = True
            if(S >= csvOutThreshold and self.__CSVOutEnable and self.__startTriggerSet):
                self.__outputToCSV()
                csvOutRateLimit = False
            if output_callback:
              output_callback(self.__arrangeSamples())
            if(S == 0):
                Samples = [[0 for _ in range(self.__packetSize+1)] for _ in range(self.bulkProcessRate)]
        self.monsoon.stopSampling()
        if(self.__CSVOutEnable):
            self.__outputToCSV()
            self.disableCSVOutput()

    def startSampling(self, samples=5000, granularity = 1, legacy_timestamp=False, calTime = 1250, output_callback=None):
        """Handle setup for sample collection.
        samples:  Number of samples to collect, independent of the stop trigger.  sampleEngine.triggers.SAMPLECOUNT_INFINITE to function solely through triggers.
        granularity:  Samples to store.  1 = 1:1, 10 = store 1 out of every 10 samples, etc.  
        legacy_timestamp: if true, use time.time() for timestamp instead of currentTime - startTime
        """
        if(self.__errorMode == ErrorHandlingModes.off):
            self.__startSampling(samples,granularity,legacy_timestamp,output_callback=output_callback)
        else:
            try:
                self.__startSampling(samples,granularity,legacy_timestamp,calTime,output_callback)
            except KeyboardInterrupt:
                print("Caught keyboard interrupt, test ending adruptly.")
                self.monsoon.stopSampling()
                if(self.__CSVOutEnable):
                    self.__outputToCSV()
                    self.disableCSVOutput()
            except usb.core.USBError:
                print("Caught disconnection event. Test restarting with default parameters")
                self.monsoon.Reconnect()
                self.monsoon.stopSampling()
                if(self.__CSVOutEnable):
                    self.__outputToCSV()
                    self.disableCSVOutput()
                    self.enableCSVOutput(self.__outputFilename)
                self.startSampling(samples,granularity, legacy_timestamp,calTime,output_callback)

            except Exception as e:
                print("Error: Unknown exception caught.  Test failed.")
                self.monsoon.stopSampling()
                if(self.__CSVOutEnable):
                    self.__outputToCSV()
                    self.disableCSVOutput()
                raise Exception(e.args)


    def periodicStartSampling(self,calTime=1250):
        """Causes the Power Monitor to enter sample mode, but doesn't actively collect samples.
        Call periodicCollectSamples() periodically get measurements.
        """
        self.__Reset()
        self.__sampleLimit = triggers.SAMPLECOUNT_INFINITE
        self.__granularity = 1
        if(self.__CSVOutEnable):
            self.outputCSVHeaders()
        Samples = [[0 for _ in range(self.__packetSize+1)] for _ in range(self.bulkProcessRate)]
        self.__startTime = time.time()
        self.monsoon.StartSampling(calTime,triggers.SAMPLECOUNT_INFINITE)
        if not self.__startupCheck():
            self.monsoon.stopSampling()
            return False
        result = self.getSamples()
        return result


    def periodicCollectSamples(self,samples=100,legacy_timestamp = False):
        """Start sampling with periodicStartSampling(), then call this to collect samples.
        Returns the most recent measurements made by the Power Monitor.
        samples:  Number of samples to collect.
        legacy_timestamp: if true, use time.time() for timestamp instead of currentTime - startTime"""
        #TODO:  This normally returns 3-5 samples over the requested number of samples.
        self.__sampleCount = 0
        self.__sampleLimit = samples
        self.__stopTriggerSet = False
        self.monsoon.BulkRead() #Clear out stale buffer
        Samples = [[0 for _ in range(self.__packetSize+1)] for _ in range(1)]
        while not self.__stopTriggerSet:
            S = self.__sampleLoop(0,Samples,1,legacy_timestamp)
        if(self.__CSVOutEnable and self.__startTriggerSet):
            self.__outputToCSV() #Note that this will cause the script to return nothing.
        result = self.getSamples()
        return result

    def periodicStopSampling(self, closeCSV=False):
        """Performs cleanup tasks when finished sampling.
        closeCSV:  Closes the CSV file along with exiting sample mode."""
        if(self.__CSVOutEnable and self.__startTriggerSet):
            self.__outputToCSV()
            if(closeCSV):
                self.disableCSVOutput()
        self.monsoon.stopSampling()

