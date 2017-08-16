#Special thanks to Tom Christie for providing this template.
#Adapted from the instructions at https://tom-christie.github.io/articles/pypi/

from setuptools import setup, find_packages  # Always prefer setuptools over distutils
from codecs import open  # To use a consistent encoding
from os import path
import subprocess
from setuptools.command.install import install

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README'), encoding='utf-8') as f:
    long_description = f.read()

#see http://www.niteoweb.com/blog/setuptools-run-custom-code-during-install
#This is so we can call "make" automatically during setup
class MyInstall(install):
    def run(self):
        # try:
            # subprocess.call(['make'],cwd=path.join(here,'placeholder_C_code'))
        # except Exception as e:
            # print e
            # print "Error compiling t2p.c.   Try running 'make'."
            # exit(1)
        # else:
        install.run(self)

setup(
    name='Pymonsoon',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # http://packaging.python.org/en/latest/tutorial.html#version
    version='0.1.0',

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
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5'
    ],

    # What does your project relate to?
    keywords='Power measurement',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages = find_packages(exclude=['build', 'docs', 'templates']),
    #package_dir={'vfclust': 'vfclust'},

    # List run-time dependencies here.  These will be installed by pip when your
    # project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/technical.html#install-requires-vs-requirements-files
    #install_requires=['NLTK'],

    # If there are data files included in your packages that need to be
    # installed in site-packages, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # include_package_data=True,
    # # relative to the vfclust directory
    # package_data={
        # 'vfclust':[
             # 'Makefile'],
        # 'data':
             # ['data/animals_lemmas.dat',
             # 'data/animals_names.dat',
             # 'data/animals_names_raw.dat',
             # 'data/cmudict.0.7a.tree',
             # 'data/modified_cmudict.dat',
             # 'data/animals_term_vector_dictionaries/term_vectors_dict91_cpickle.dat',
             # ],
        # 'data/EOWL':
            # ['data/EOWL/english_words.txt',
             # 'data/EOWL/EOWL Version Notes.txt',
             # 'data/EOWL/The English Open Word List.pdf'
            # ],
        # 'example':
            # ['example/EXAMPLE.csv',
             # 'example/EXAMPLE.TextGrid',
             # 'example/EXAMPLE_sem.csv',
             # 'example/EXAMPLE_sem.TextGrid'],
        # 't2p':
            # ['t2p/t2p.c',
             # 't2p/t2pin.tmp'
             # ],
    # },

    #run custom code
    #cmdclass={'install': MyInstall},

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages.
    # see http://_docs.python.org/3.4/distutils/setupscript.html#installing-additional-files
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[
    #     ('my_data',['data_file']),
    # ],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    # entry_points={
       # 'console_scripts': [
           # 'vfclust = vfclust.vfclust:main',
       # ],
    # }

)