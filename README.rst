
----

THIS PROJECT NEEDS A NEW OWNER
==============================

I no longer have the bandwidth or capability to maintain this project. Please open an issue or ping
me directly if you'd like to take it over.

----

Introduction
============
Command line utility to interact with your jira instance. 

.. |travis-ci| image:: https://img.shields.io/travis/alisaifee/jira-cli/master.svg?style=flat-square
   :alt: build status
   :target: https://travis-ci.org/#!/alisaifee/jira-cli
.. |codecov| image:: https://img.shields.io/codecov/c/github/alisaifee/jira-cli/master.svg?style=flat-square
    :target: https://codecov.io/gh/alisaifee/jira-cli
.. |license| image:: https://img.shields.io/pypi/l/jira-cli.svg?style=flat-square
    :target: https://pypi.python.org/pypi/jira-cli
.. |pypi| image:: https://img.shields.io/pypi/v/jira-cli.svg?style=flat-square
    :target: https://pypi.python.org/pypi/jira-cli

.. _read the docs: https://jira-cli.readthedocs.org


|travis-ci| |codecov| |pypi| |license|

Documentation at `read the docs`_


Deprecation warning
===================
jira-cli, as of version ``2.1`` defaults to using the new command line interface.
The command line interface presented by versions up to ``0.4.2`` will be maintained (but only accessible if the ``--v1``
flag is passed in or the following snippet exists in the config file)::


    [jira]
    v1 = True



