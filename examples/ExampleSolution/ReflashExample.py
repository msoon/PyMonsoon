import Monsoon.reflash as reflash


######################################
# Reflash unit with USB Protocol firmware
######################################
#Mon = reflash.bootloaderMonsoon()
#Mon.setup_usb()
#Header, Hex = Mon.getHeaderFromFWM('../../Firmware/LVPM_RevE_Prot_1_Ver25_beta.fwm')
#if(Mon.verifyHeader(Header)):
#    Mon.writeFlash(Hex)

######################################
# Return to the serial protocol firmware.
######################################
Mon = reflash.bootloaderMonsoon()
Mon.setup_usb()
Hex = Mon.getHexFile('C:\Users\jared\Documents\Git Repos\Firmware\HVPM28.hex')
Mon.writeFlash(Hex)