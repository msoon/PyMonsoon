import math

class calibrationData(object):
    """Stores calibration data for every Monsoon channel.
    Uses a rolling queue of size self.calsToKeep to store the last x measurements."""
    def __init__(self, calsToKeep=5):

        self.calsToKeep = calsToKeep
        self.refCalFine = [0 for x in range(self.calsToKeep)]
        self.refCalCoarse = [0 for x in range(self.calsToKeep)]
        self.zeroCalFine = [0 for x in range(self.calsToKeep)]
        self.zeroCalCoarse = [0 for x in range(self.calsToKeep)]
        self.refCalFineIndex = 0
        self.zeroCalFineIndex = 0
        self.refCalCourseIndex = 0
        self.zeroCalCourseIndex = 0
        self.coarseRefCalibrated = False
        self.coarseZeroCalibrated = False
        self.fineRefCalibrated = False
        self.fineZeroCalibrated = False
        pass
    def clear(self):
        self.refCalFine = [0 for x in range(self.calsToKeep)]
        self.refCalCoarse = [0 for x in range(self.calsToKeep)]
        self.zeroCalFine = [0 for x in range(self.calsToKeep)]
        self.zeroCalCoarse = [0 for x in range(self.calsToKeep)]
        self.refCalFineIndex = 0
        self.zeroCalFineIndex = 0
        self.refCalCourseIndex = 0
        self.zeroCalCourseIndex = 0
        self.coarseRefCalibrated = False
        self.coarseZeroCalibrated = False
        self.fineRefCalibrated = False
        self.fineZeroCalibrated = False

    def __getCal(self, list):
        if(self.calibrated()):
            return sum(list)/len(list)
        else:#We shouldn't be calling this at all if we aren't calibrated.
            raise ValueError("Attempted to get calibration data when not calibrated.")
    def calibrated(self):
        return self.coarseRefCalibrated and self.coarseZeroCalibrated and self.fineRefCalibrated and self.fineZeroCalibrated
    def getRefCal(self, Coarse):
        """Get average reference calibration measurement"""
        if(Coarse):
            list = self.refCalCoarse
        else:
            list = self.refCalFine
        return self.__getCal(list)

    def getZeroCal(self, Coarse):
        """Get average zero calibration value"""
        if(Coarse):
            list = self.zeroCalCoarse
        else:
            list = self.zeroCalFine
        return self.__getCal(list)


    def __addCal(self, list, value, index):

        list[index] = value


    def addRefCal(self, value, Coarse):
        """Add reference calibration measurement."""
        if(value != 0):
            if(Coarse):
                self.__addCal(self.refCalCoarse,value,self.refCalCourseIndex)
                self.refCalCourseIndex+= 1
                if(self.refCalCourseIndex >= self.calsToKeep):
                    self.coarseRefCalibrated = True
                    self.refCalCourseIndex = 0
            else:
                self.__addCal(self.refCalFine,value,self.refCalFineIndex)
                self.refCalFineIndex+= 1
                if(self.refCalFineIndex >= self.calsToKeep):
                    self.fineRefCalibrated = True
                    self.refCalFineIndex = 0


    def addZeroCal(self, value, Coarse):
        """Add zero calibration measurement."""
        if(value != 0):
            if(Coarse):
                self.__addCal(self.zeroCalCoarse,value,self.zeroCalCourseIndex)
                self.zeroCalCourseIndex+= 1
                if(self.zeroCalCourseIndex >= self.calsToKeep):
                    self.coarseZeroCalibrated = True
                    self.zeroCalCourseIndex = 0
            else:
                self.__addCal(self.zeroCalFine,value,self.zeroCalFineIndex)
                self.zeroCalFineIndex+= 1
                if(self.zeroCalFineIndex >= self.calsToKeep):
                    self.fineZeroCalibrated = True
                    self.zeroCalFineIndex = 0
