import Monsoon.reflash as reflash
import Monsoon.HVPM as HVPM
import Monsoon.LVPM as LVPM
import time

######################################
# Reflash unit with USB Protocol firmware
######################################
#Mon = LVPM.Monsoon()
#Mon.setup_usb()
#Mon.resetToBootloader()
#time.sleep(1)

#Ref = reflash.bootloaderMonsoon()
#Ref.setup_usb()
#Header, Hex = Ref.getHeaderFromFWM('LVPM_RevE_Prot_1_Ver25_beta.fwm')
#if(Ref.verifyHeader(Header)):
#    Ref.writeFlash(Hex)

######################################
# Reflash unit with USB protocal, automatic bootloader and restart
######################################

Mon = HVPM.Monsoon()
Mon.setup_usb()
Mon.resetToBootloader()
time.sleep(1)

Ref = reflash.bootloaderMonsoon()
Ref.setup_usb()
Header, Hex = Ref.getHeaderFromFWM('HVPM_RevE_Prot1_Ver32.fwm')
if (Ref.verifyHeader(Header)):
    Ref.writeFlash(Hex)
Ref.resetToMainSection()

time.sleep(5)
Mon.setup_usb()
Mon.setPowerUpCurrentLimit(8)
Mon.setRunTimeCurrentLimit(8)
Mon.fillStatusPacket()
print("Unit number " + repr(Mon.getSerialNumber()) + " finished. New firmware revision: " + repr(Mon.statusPacket.firmwareVersion))
Mon.closeDevice()



######################################
# Return to the serial protocol firmware.
######################################
#Mon = reflash.bootloaderMonsoon()
#Mon.setup_usb()
#Hex = Mon.getHexFile('PM_RevD_Prot17_Ver20.hex')
#Mon.writeFlash(Hex)