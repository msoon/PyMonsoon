# PyMonsoon
Monsoon Power Monitor Python Library
Monsoon Website:  https://www.msoon.com/
PyPi Project: https://pypi.python.org/pypi/monsoon/

Install using 'pip install Monsoon'


# Usage Notes

This project is currently in an Alpha state.  Users are encouraged to report bugs, features requests, or other recommendations for improvement.

Legacy Hardware (Part number FTA22D, The white box) will require a firmware update before using this Library.  Example code for accomplishing this is available in /examples/ReflashExample.py.  The firmware update will render the unit incompatible with the Windows 4.X series software, and require a driver update in Windows.  

Current Hardware (Part number AAA10F, the black box) will be functional.

Windows users:  This library uses libusb to communiate with the Power Monitor.  On Windows, this requires installing the libusb filter to allow the connection code to detect the Power Monitor.  Instructions for this are available at http://libusbdotnet.sourceforge.net/V2/Index.html

