Introduction
============
Simple command line utility to interact with your jira instance. 

.. |travis-ci| image:: https://api.travis-ci.org/alisaifee/jira-cli.png
   :alt: build status
   :target: https://travis-ci.org/#!/alisaifee/jira-cli
.. |coveralls| image:: https://coveralls.io/repos/alisaifee/jira-cli/badge.png?branch=master
    :target: https://coveralls.io/r/alisaifee/jira-cli?branch=master
.. |pypi| image:: https://pypip.in/v/jira-cli/badge.png
    :target: https://crate.io/packages/jira-cli/
.. |license| image:: https://pypip.in/license/jira-cli/badge.png
    :target: https://pypi.python.org/pypi/jira-cli/

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



