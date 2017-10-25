#Special thanks to Tom Christie for providing this template.
#Adapted from the instructions at https://tom-christie.github.io/articles/pypi/

from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path
import subprocess
from setuptools.command.install import install

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='monsoon',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='0.1.65',

    description='Monsoon Power Monitor API',
    long_description=long_description,

    # The project's main homepage.
    url='https://www.msoon.com/LabEquipment/PowerMonitor/',

    # Author details
    author='Michael Brinker',
    author_email='mikeb@msoon.com',

    # Choose your license
    license='MIT',

    # See https://PyPI.python.org/PyPI?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",

        # Pick your license as you wish (should match "license" above)
        "License :: OSI Approved :: GNU General Public License (GPL)",

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ],

    # What does your project relate to?
    keywords='Power measurement',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages = find_packages(exclude=['build', 'docs', 'templates','Main.py','reflashMain.py']),

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    install_requires=['numpy','pyusb','libusb1'],

    # If there are data files included in your packages that need to be
    # installed in site-packages, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # include_package_data=True,
    # # relative to the vfclust directory
     package_data={
         'examples':
              ['examples/SimpleSamplingExample.py',
               'examples/ReflashExample.py',
			   'examples/LVPM_RevE_Prot_1_Ver25_beta.fwm'
              ],
         'docs':
             ['docs/API.pdf',
              'docs/Linux/reflashinstructions.txt',
              'docs/Windows/driverInstall.docx',
			  'docs/Windows/reflash.docx'
             ],
		 'Firmware':
		 [
		 'Firmware/Firmware.zip'
		 ],
		 'Drivers':
		 [
		 'docs/Drivers/HVPM/powermonitor.cat',
		 'docs/Drivers/HVPM/PowerMonitor.inf',
		 'docs/Drivers/HVPM/WdfCoinstaller01011.dll',
		 'docs/Drivers/HVPM/winusbcoinstaller2.dll'
		 ]
		 
		 
     },

)