import Monsoon.reflash as reflash
import Monsoon.HVPM as HVPM
import time

"""This example assumes multiple Power Monitors are connected to the same computer and powered up normally.
It shows how to reflash units programmatically, so there's no need for manual power cycling."""

def reflashUnit(serialno = None):
    print("Reflashing unit number " + repr(serialno))
    Mon = HVPM.Monsoon()
    Mon.setup_usb(serialno)
    Mon.resetToBootloader()

    time.sleep(1) #Gives time for unit re-enumeration.  This may need to be longer on some machines.
    Ref = reflash.bootloaderMonsoon()
    Ref.setup_usb()
    Header, Hex = Ref.getHeaderFromFWM('../../Firmware/debug/HVPM27.fwm')
    if(Ref.verifyHeader(Header)):
        Ref.writeFlash(Hex)
    Ref.writeFlash(Hex)
    Ref.resetToMainSection()

    time.sleep(1) #Gives time for unit re-enumeration.  This may need to be longer on some machines.
    #Verify the firmware was flashed properly.
    Mon.setup_usb(serialno)
    Mon.fillStatusPacket()
    print("Unit number " + repr(Mon.getSerialNumber()) + " finished.  New firmware revision: " + repr(Mon.statusPacket.firmwareVersion))
    Mon.closeDevice()

def main():
    Dev = HVPM.Monsoon()
    serialNumbers = Dev.enumerateDevices()
    for serialno in serialNumbers:
        reflashUnit(serialno)

if __name__ == "__main__":
    main()