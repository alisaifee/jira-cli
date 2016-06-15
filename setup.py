"""
setup.py for jira-cli
"""
__author__ = "Ali-Akber Saifee"
__email__ = "ali@indydevs.org"
__copyright__ = "Copyright 2014, Ali-Akber Saifee"

import os
import sys

from setuptools import setup, find_packages

import jiracli

import versioneer

versioneer.versionfile_source = "jiracli/_version.py"
versioneer.versionfile_build = "jiracli/version.py"
versioneer.tag_prefix = ""
versioneer.parentdir_prefix = "jiracli-"

this_dir = os.path.abspath(os.path.dirname(__file__))
REQUIREMENTS = [k for k in open(
    os.path.join(this_dir, 'requirements/main.txt')
                ).read().splitlines() if k
]

extra = {}
if sys.version_info >= (3,):
    extra['use_2to3'] = True

setup(name='jira-cli',
     author=__author__,
     author_email=__email__,
     url="http://github.com/alisaifee/jira-cli",
     license="MIT",
     description = "command line utility for interacting with jira",
     long_description = open("README.rst").read(),
     classifiers = [k for k in open("CLASSIFIERS").read().split("\n") if k],
     packages = find_packages(exclude=['ez_setup','tests']),
     include_package_data = True,
     zip_safe = False,
     version=versioneer.get_version(),
     cmdclass=versioneer.get_cmdclass(),
     install_requires = REQUIREMENTS,
     entry_points = {
         'console_scripts' : [
             'jira-cli = jiracli.interface:cli',
             ]
        },
    **extra
     )

