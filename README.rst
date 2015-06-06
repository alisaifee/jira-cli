Introduction
============
Simple command line utility to interact with your jira instance. 

.. |travis-ci| image:: https://img.shields.io/travis/alisaifee/jira-cli/master.svg?style=flat-square
   :alt: build status
   :target: https://travis-ci.org/#!/alisaifee/jira-cli
.. |coveralls| image:: https://img.shields.io/coveralls/alisaifee/jira-cli/master.svg?style=flat-square
    :target: https://coveralls.io/r/alisaifee/jira-cli?branch=master
.. |license| image:: https://img.shields.io/pypi/l/jira-cli.svg?style=flat-square
    :target: https://pypi.python.org/pypi/jira-cli
.. |pypi| image:: https://img.shields.io/pypi/v/jira-cli.svg?style=flat-square
    :target: https://pypi.python.org/pypi/jira-cli

.. _read the docs: https://jira-cli.readthedocs.org


|travis-ci| |coveralls| |pypi| |license|

Documentation at `read the docs`_

Deprecation warning
===================
jira-cli, as of version ``2.0.0-pre`` has been completely rewritten (including the command line interface).
The command line interface presented by versions up to ``0.4.2`` will be maintained (and presented
by default) until the official release of version ``2.0``.

If you'd like to try out the new interface, add the ``--v2`` command line argument or add the following
snippet to your ``~/.jira-cli/config.cfg`` file::

    [jira]
    v2 = True



