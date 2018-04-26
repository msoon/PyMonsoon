class OpCodes:
    """USB Control Transfer operation codes"""
    setMainFineResistorOffset=0x02 #LVPM Calibration value, 8-bits signed, ohms = 0.05 + 0.0001*offset
    setMainCoarseResistorOffset=0x11 #LVPM Calibration value, 8-bits signed, ohms = 0.05 + 0.0001*offset
    setUsbFineResistorOffset=0x0D #LVPM Calibration value, 8-bits signed, ohms = 0.05 + 0.0001*offset
    setUsbCoarseResistorOffset=0x12 #LVPM Calibration value, 8-bits signed, ohms = 0.05 + 0.0001*offset
    setAuxFineResistorOffset=0x0E #LVPM Calibration value, 8-bits signed, ohms = 0.1 + 0.0001*offset
    setAuxCoarseResistorOffset=0x13 #LVPM Calibration value, 8-bits signed, ohms = 0.1 + 0.0001*offset
    calibrateMainVoltage=0x03 #Internal voltage calibration, affects accuracy of setHVMainVoltage
    resetPowerMonitor=0x05 #Reset the PIC.  Causes disconnect.
    setPowerupTime=0x0C #time in milliseconds that the powerup current limit is in effect.
    setTemperatureLimit=0x29 #Temperature limit in Signed Q7.8 format
    setUsbPassthroughMode=0x10 #Sets USB Passthrough mode according to value.  Off = 0, On = 1, Auto = 2
    setMainFineScale = 0x1A #HVPM Calibration value, 32-bits, unsigned
    setMainCoarseScale = 0x1B #HVPM Calibration value, 32-bits, unsigned
    setUSBFineScale = 0x1C #HVPM Calibration value, 32-bits, unsigned
    setUSBCoarseScale = 0x1D #HVPM Calibration value, 32-bits, unsigned
    setAuxFineScale = 0x1E #HVPM Calibration value, 32-bits, unsigned
    setAuxCoarseScale = 0x1F #HVPM Calibration value, 32-bits, unsigned
    setVoltageChannel = 0x23 #Sets voltage channel:  Value 00 = Main & USB voltage measurements.  Value 01 = Main & Aux voltage measurements
    SetPowerUpCurrentLimit = 0x43 #Sets power-up current limit.  HV Amps = 15.625*(1.0-powerupCurrentLimit/65535) #LV amps = 8.0*(1.0-powerupCurrentLimit/1023.0)
    SetRunCurrentLimit = 0x44 #Sets runtime current limit        HV Amps = 15.625*(1.0-powerupCurrentLimit/65535) #LV amps = 8.0*(1.0-powerupCurrentLimit/1023.0)
    setMainVoltage = 0x41 # Voltage = value * 1048576
    getSerialNumber = 0x42
    SetMainFineZeroOffset=0x25 #Zero-level offset
    SetMainCoarseZeroOffset = 0x26 #Zero-level offset
    SetUSBFineZeroOffset = 0x27 #Zero-level offset
    SetUSBCoarseZeroOffset = 0x28 #Zero-level offset
    FirmwareVersion = 0xC0 #Read-only, gets the firmware version
    ProtocolVersion = 0xC1 #Read-only, gets the Protocol version
    HardwareModel = 0x45 #0 = unknown, 1 = LV, 2 = HV
    getStartStatus = 0xC4 
    dacCalLow = 0x88 #2.5V ADC Reference Calibration
    dacCalHigh = 0x89 #4.096V ADC Reference Calibration
    Stop = 0xFF

class ReturnCodes:
    """Status return codes"""
    #TODO:  Should really consolidate this with a few other misc values.
    ERROR = 0xfffffffE
    CURRENT_FIRMWARE_REV = 32
class HardwareModel:
    """Hardware Model Types"""
    UNKNOWN = 0
    LVPM = 1
    HVPM = 2
class Control_Codes:
    """USB Protocol codes."""
    USB_IN_PACKET = 0xC0
    USB_OUT_PACKET = 0x40
    USB_REQUEST_START = 0x02
    USB_REQUEST_STOP = 0x03
    USB_SET_VALUE = 0x01
    USB_REQUEST_RESET_TO_BOOTLOADER = 0xFF

class Conversion:
    """Values used for converting from desktop to the PIC"""
    FLOAT_TO_INT = 1048576
class USB_Passthrough:
    """Values for setting or retrieving the USB Passthrough mode."""
    Off = 0
    On = 1
    Auto = 2
class VoltageChannel:
    """Values for setting or retrieving the Voltage Channel."""
    Main = 0 
    USB = 1
    Aux = 2

class statusPacket:
    """Values stored in the Power Monitor EEPROM.  Each corresponds to an opcode"""
    firmwareVersion = 0 #Firmware version number.
    protocolVersion = 0 #Protocol version number.
    temperature = 0 #Current temperature reading from the board.
    serialNumber = 0 #Unit's serial number.
    powerupCurrentLimit = 0  #Max current during startup before overcurrent protection circuit activates.  LVPM is 0-8A, HVPM is 0-15A.
    runtimeCurrentLimit = 0 #Max current during runtime before overcurrent protection circuit activates.  LVPM is 0-8A, HVPM is 0-15A.
    powerupTime = 0 #Time in ms the powerupcurrent limit will be used.
    temperatureLimit = 0 #Temperature limit in Signed Q7.8 format
    usbPassthroughMode = 0 # Off = 0, On = 1, Auto = 2
    
    mainFineScale = 0 #HVPM Calibration value, 32-bits, unsigned
    mainCoarseScale = 0#HVPM Calibration value, 32-bits, unsigned
    usbFineScale = 0#HVPM Calibration value, 32-bits, unsigned
    usbCoarseScale = 0#HVPM Calibration value, 32-bits, unsigned
    auxFineScale = 0#HVPM Calibration value, 32-bits, unsigned
    auxCoarseScale = 0#HVPM Calibration value, 32-bits, unsigned
    
    mainFineZeroOffset = 0 #HVPM-only, Zero-level offset
    mainCoarseZeroOffset = 0 #HVPM-only, Zero-level offset
    usbFineZeroOffset = 0 #HVPM-only, Zero-level offset
    usbCoarseZeroOffset = 0 #HVPM-only, Zero-level offset
    hardwareModel = 0 #HVPM-only, Zero-level offset

    mainFineResistorOffset = 0 #signed, ohms = 0.05 + 0.0001*offset
    mainCoarseResistorOffset = 0 #signed, ohms = 0.05 + 0.0001*offset
    usbFineResistorOffset = 0 #signed, ohms = 0.05 + 0.0001*offset
    usbCoarseResistorOffset = 0 #signed, ohms = 0.05 + 0.0001*offset
    auxFineResistorOffset = 0 #signed, ohms = 0.10 + 0.0001*offset
    auxCoarseResistorOffset = 0 #signed, ohms = 0.10 + 0.0001*offset

    dacCalLow = 0
    dacCalHigh = 0

class BootloaderCommands:
    """Bootloader opcodes.  Used when reflashing the Power Monitor"""
    ReadVersion = 0x00
    ReadFlash = 0x01
    WriteFlash = 0x02
    EraseFlash = 0x03
    ReadEEPROM = 0x04
    WriteEEPROM = 0x05
    ReadConfig = 0x06
    WriteConfig = 0x07
    Reset = 0xFF

class BootloaderMemoryRegions:
    """Memory regions of the PIC18F4550"""
    Flash = 0x00
    IDLocs = 0x20
    Config = 0x30
    EEPROM = 0xf0

class hexLineType:
    """line types used in the intel hex format.  Used when reflashing the Power Monitor."""
    Data = 0
    EndOfFile = 1
    ExtendedSegmentAddress = 2
    StartSegmentAddress = 3
    ExtendedLinearAddress = 4
    StartLinearAddress = 5

class SampleType(object):
    """Corresponds to the sampletype field from a sample packet."""
    Measurement = 0x00
    ZeroCal = 0x10
    invalid = 0x20
    refCal = 0x30

