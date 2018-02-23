import platform
import usb.core
import usb.util
import struct
from Monsoon import Operations as op
from copy import deepcopy
import numpy as np

import array
DEVICE = None
DEVICE_TYPE = None
epBulkWriter = None
epBulkReader = None
VID = '0x2ab9'
PID = '0xffff'

class bootloaderMonsoon(object):
    def __init__(self,*args, **kwargs):
        pass

    def setup_usb(self):
        """Sets up the USB connection."""
        global DEVICE
        global VID
        global PID

        DEVICE = usb.core.find(idVendor=0x2AB9,idProduct=0xFFFF)
        if DEVICE is None:#If not a LVPM, look for an HVPM.
            DEVICE = usb.core.find(idVendor=0x04d8,idProduct=0x000b)
            VID = '0x4d8'
            PID = '0xb'
        if "Linux" == platform.system():
            try:
                DEVICE.detach_kernel_driver(0)
            except:
                pass # already unregistered

    def __bootCommand(self,Command,length,address,data):
        """Sends boot command."""
        sendData = []
        sendData.append(Command)
        sendData.append(length)
        sendData.append(address[2])
        sendData.append(address[1])
        sendData.append(address[0])
        for i in range(0,len(data)):
            sendData.append(data[i])
        for i in range(len(data),length):
            sendData.append(0)
        epBulkWriter.write(sendData,timeout=10000)
        ret = epBulkReader.read(length+5,timeout=10000)
        return ret




    def writeFlash(self, hex_):
        """Writes a hex file to the Power Monitor's PIC.  Uses Intel HEX file format."""
        Flash, EEPROM,IDlocs,Config  = self.__formatHex(hex_)
        print("Erasing Flash...")
        self.__writeRegion(op.BootloaderMemoryRegions.Flash,op.BootloaderCommands.EraseFlash,0x0800,Flash,None)
        print("Writing Flash...")
        if(self.__writeRegion(op.BootloaderMemoryRegions.Flash,op.BootloaderCommands.WriteFlash,0x0800,Flash,op.BootloaderCommands.ReadFlash)):
            print("Flash written OK")
        #Don't actually erase the EEPROM, this would wipe out all of the calibration data.
        #if(self.writeRegion(op.BootloaderMemoryRegions.EEPROM,op.BootloaderCommands.WriteEEPROM,0x0000,EEPROM,op.BootloaderCommands.ReadEEPROM)):
        #    print("EEPROM written OK")
        if(self.__writeChunk(op.BootloaderMemoryRegions.IDLocs,op.BootloaderCommands.WriteFlash,0x0000,IDlocs,op.BootloaderCommands.ReadFlash)):
            print("IDLocs written OK")
        if(self.__writeChunk(op.BootloaderMemoryRegions.Config,op.BootloaderCommands.WriteConfig,0x0000,Config,op.BootloaderCommands.ReadConfig)):
            print("Config written OK")


    def __writeRegion(self, memoryRegion,command,addressStart,regionData,errorCheckCommand):
        """Writes information to a memory region."""
        address = [0 for _ in range(3)]
        data = [0 for _ in range(16)]
        result = True
        progressThresholds = [x*10 for x in range(11)]
        progressindex = 0
        len(regionData)
        for i in range(addressStart, len(regionData), 16):
            memoryIndex = struct.unpack("BBBB",struct.pack('I', i))
            address[0] = memoryRegion
            address[1] = memoryIndex[1]
            address[2] = memoryIndex[0]
            data = regionData[i:i+16]
            #self.bootCommand(op.BootloaderCommands.EraseFlash,16,address,[])
            self.__bootCommand(command,len(data),address,data)
            if(errorCheckCommand != None):
                dataout = self.__bootCommand(errorCheckCommand,16,address,[])
                dataout = dataout[5:len(dataout)]
                if not self.__compare(data,dataout):
                    result = False
                    print("Write error")
            percentComplete = (i*1.0 / len(regionData)) * 100
            if(progressThresholds[progressindex] < percentComplete):
                print('%.0f percent complete' % percentComplete)
                progressindex += 1
        return result

    def __writeChunk(self, memoryRegion,command,addressStart,regionData,errorCheckCommand):
        result = True
        address = [0 for _ in range(3)]
        address[0] = memoryRegion
        address[1] = 0
        address[2] = 0
        data = regionData
        if(memoryRegion != op.BootloaderMemoryRegions.Config):
            self.__bootCommand(op.BootloaderCommands.EraseFlash,16,address,[])
        self.__bootCommand(command,len(data),address,data)
        #dataout = self.bootCommand(errorCheckCommand,16,address,[])
        #dataout = dataout[5:len(dataout)]
        #if not self.compare(data,dataout):
        #    result = False
        #    print("Reflash Write error")
        return result

    def __compare(self,data,dataout):
        """Compare read data to the data we think we wrote."""
        if(data == None or dataout == None):
            return False
        if(len(data) != len(dataout)):
            return False
        for i in range(len(data)):
            if(data[i] != dataout[i]):
                return False
        return True
    def __byteLine(self, line):
        """Translate a HEX file line into address, linetype, data, and checksum"""
        output = []
        for offset in range(1,len(line)-1,2):
            output.append(struct.unpack("B",struct.pack('B',np.int(line[offset:offset+2],16))[0])[0])
        address = []
        length = output[0]
        address.append(output[1])
        address.append(output[2])
        type_ = output[3]
        Data = output[4:4+length]
        checksum = output[len(output)-1]
        return address, type_, Data, checksum


    def getHeaderFromFWM(self, filename):
        """Strips the header from a Monsoon FWM file, returns the HEX file and the formatted header.
        Header format [VID,PID,Rev,Model]"""
        f = open(filename,'r')
        hex_ = f.read()
        f.close()

        headerEnd = hex_.find(':')
        header = hex_[0:headerEnd]
        offset = 7
        count = array.array('B', header[offset])[0]
        offset += 1
        hex_ = hex_[headerEnd:len(hex_)]
        outHeader = [0 for _ in range(4)]
        headers = []
        i = 0
        for i in range(count):
            outHeader[0] = array.array('H', header[offset:offset+2])[0] #VID
            offset += 2
            outHeader[1] = array.array('H', header[offset:offset+2])[0] #PID
            offset += 2
            outHeader[2] = array.array('H', header[offset:offset+2])[0] #Rev
            offset += 2
            outHeader[3] = array.array('H', header[offset:offset+2])[0] #Model
            offset += 2
            test = deepcopy(outHeader)

            headers.append(test)
            i+= 1
        return headers, hex_

    def getHexFile(self, filename):
        """Reads an Intel HEX file."""
        f = open(filename,'r')
        hex_ = f.read()
        f.close()
        return hex_

    def __formatHex(self,hex_):
        """Takes raw hex_ input, and turns it into an array of hex_ lines."""
        output = []
        lineEnd = hex_.find('\n')
        while lineEnd > 0:
            output.append(hex_[0:lineEnd])
            hex_ = hex_[lineEnd+1:len(hex_)]
            lineEnd = hex_.find('\n')
        Flash, EEPROM,IDlocs,Config = self.__formatAsPICFlash(output)
        return  Flash, EEPROM,IDlocs,Config

    def __formatAsPICFlash(self, hex_):
        """Formats an array of hex_ lines as PIC memory regions."""
        flash = [0xff for _ in range(32768)]
        EEPROM = [0xff for _ in range(256)]
        IDlocs = [0xff for _ in range(16)]
        Config  = [0xff for _ in range(14)]
        addressMSB = 0
        for line in hex_:
            address, type_, Data, _ = self.__byteLine(line)
            intAddress = struct.unpack("h",struct.pack("BB", address[1],address[0]))[0]
            if(type_ == op.hexLineType.ExtendedLinearAddress):
                addressMSB = Data[1]
            if(type_ == op.hexLineType.Data):
                if(addressMSB == op.BootloaderMemoryRegions.Flash):
                    for byte in Data:
                        flash[intAddress] = byte
                        intAddress += 1
                if(addressMSB == op.BootloaderMemoryRegions.EEPROM):
                    intAddress = address[1]
                    for byte in Data:
                        EEPROM[intAddress] = byte
                        intAddress += 1
                if(addressMSB == op.BootloaderMemoryRegions.IDLocs):
                    intAddress = address[1]
                    for byte in Data:
                        IDlocs[intAddress] = byte
                        intAddress += 1
                if(addressMSB == op.BootloaderMemoryRegions.Config):
                    intAddress = address[1]
                    for byte in Data:
                        Config[intAddress] = byte
                        intAddress += 1
        return flash, EEPROM, IDlocs, Config

    def verifyHeader(self, headers):
        """Verifies the header matches the physical hardware being reflashed."""
        for head in headers:
            if(hex(head[0]) == VID and hex(head[1]) == PID):
                return True
        return False

    def resetToMainSection(self):
        """
        Exits bootloader mode and returns to normal mode.
        This will disconnect the device, and you should reconnect with HVPM.py or LVPM.py, depending on your hardware.
        Most LVPM units have an older version of the bootloader, and this command may be nonfunctional on them.  
        In that case, just manually power cycle the unit."""
        wValue = 0
        wIndex = 0
        wLength = 0
        try:
            self.__bootCommand(op.BootloaderCommands.Reset,1,[0,0,0],[])
        except:
            #This will always throw an exception because it disconnects the device and re-enumerates as a normal Power Monitor
            print("Resetting to Main Section.")

