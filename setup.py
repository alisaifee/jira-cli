"""
setup.py for jira-cli
"""
__author__ = "Ali-Akber Saifee"
__email__ = "ali@indydevs.org"

import os
import sys
from setuptools import setup, find_packages, Command

default_version="0.1"
def get_version_from_tag():
    is_tag = os.popen("git describe").read().strip()
    if not is_tag:
        return default_version
    return is_tag

setup(name='jira-cli',
     author="Ali-Akber Saifee",
     author_email="ali@indydevs.org",
     url="http://hg.indydevs.org/jira-cli",
     version = get_version_from_tag(),
     description = "command line utility for interacting with jira",
     long_description = open("README").read(),
     packages = find_packages(exclude=['ez_setup']),
     include_package_data = True,
     package_data = {
            '':[ 'README' ],
         },
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
     )

