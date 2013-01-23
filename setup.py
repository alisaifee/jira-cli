"""
setup.py for jira-cli
"""
__author__ = "Ali-Akber Saifee"
__email__ = "ali@mig33global.com"
__copyright__ = "Copyright 2013, ProjectGoth"

import os
import sys
from setuptools import setup, find_packages, Command
import jiracli

extra = {}
if sys.version_info >= (3,):
    extra['use_2to3'] = True

setup(name='jira-cli',
     author=__author__,
     author_email=__email__,
     url="http://github.com/mig33/jira-cli",
     license="MIT",
     version = jiracli.__version__,
     description = "command line utility for interacting with jira",
     long_description = open("README.rst").read(),
     classifiers = [k for k in open("CLASSIFIERS").read().split("\n") if k],
     packages = find_packages(exclude=['ez_setup']),
     include_package_data = True,
     zip_safe = False,
     install_requires =[
         'setuptools',
         'termcolor'
         ],
     entry_points = {
         'console_scripts' : [
             'jira-cli = jiracli.cli:main',
             ]
        },
    **extra
     )

