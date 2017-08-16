PyMonsoon was developed using Python 2.7, and tested using Python 3.5.

For setup in a windows environment, refer to the instructions in the 'Windows Instructions' folder.  

Dependencies:
Numpy:  http://www.numpy.org/
or install using 'pip install numpy'

pyUSB:  https://github.com/walac/pyusb
or install using 'pip install pyusb'

libusb 1.0: http://www.libusb.org/wiki/libusb-1.0
or install using 'pip install libusb1'

pyUSB also supports libusb 0.1 and OpenUSB as backends, but those haven't been tested with this script.

Preparing your environment:

1. On windows, in order for any device to be detected by libusb, you will need to install the libusb filter, which can be downloaded from https://sourceforge.net/projects/libusb-win32/  Since the reflash mode and normal mode are considered different devices with different PID's and VID's, it will be necessary to install a separate filter for each.  This step should not be necessary in a Linux environment.

2. Ensure the hardware is loaded with the most recent firmware.  Most units sold will be loaded with the old serial protocol (Ver 20), and this script is only compatible with the USB protocol (Ver 20).  As of the time of these instructions, the proper firmware file to load is LVPM_RevE_Prot1_Ver21_Beta.fwm.  Instructions are available in the 'Reflash Instructions' document.


Instructions for use:

1. create a Monsoon object based on the hardware you're using.  The currently available hardware (Part number FTA22D) is referred to as the Low Voltage Power Monitor, or LVPM.  

2. Call setup_usb().  This will find one device connected to your computer, it currently does not support multiple device.

3. Use set functions to set up the Power Monitor appropriate to your needs (enable voltage, set current limits, USB passthrough mode, etc)

4. create a sampleEngine object to handle sample collection.  Use the enableChannel or disableChannel functions to select which measurement channels will be output.

5. call engine.enableCSVOutput("filename.csv") to select the output.  At the moment, only csv output is supported.

6. call engine.startSampling(numSamples) to collect measurements.  
