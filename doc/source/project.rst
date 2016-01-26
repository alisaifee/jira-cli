Development
===========

Project resources
-----------------

.. only:: html

    - Source : `Github`_
    - Continuous Integration: |travis|
    - Test coverage: |coveralls|
    - PyPi: |crate| / `pypi <https://pypi.python.org/pypi/jira-cli>`_

.. only:: latex

    - Source : `Github`_
    - Continuous Integration: `Travis-CI <https://travis-ci.org/alisaifee/jira-cli>`_
    - Test coverage: `Coveralls <https://coveralls.io/r/alisaifee/jira-cli>`_
    - PyPi: `pypi <https://pypi.python.org/pypi/jira-cli>`_


.. _Github: http://github.com/alisaifee/jira-cli

.. |travis| image:: https://travis-ci.org/alisaifee/jira-cli.png?branch=rewrite
    :target: https://travis-ci.org/alisaifee/jira-cli
    :alt: Travis-CI

.. |coveralls| image:: https://coveralls.io/repos/alisaifee/jira-cli/badge.png?branch=rewrite
    :target: https://coveralls.io/r/alisaifee/jira-cli?branch=rewrite
    :alt: Coveralls

.. |crate| image:: https://pypip.in/v/jira-cli/badge.png
    :target: https://crate.io/packages/jira-cli/
    :alt: pypi

.. note::

    jira-cli is tested on python version 2.7


.. _rewrite:

Rewrite
-------

The project was originally written against a ``3.x`` version of jira which only
required support for the original ``soap rpc`` interface. With subsequent releases
of jira the ``json rest`` api become the recommended method of communicating
with a jira installation and the need to rewrite jira-cli became almost necessary
given that the original implementation did not cater for a multi-protocol approach.

The original implementation was also not at all testable and provided a very flat command
approach which led to numerous options and arguments being presented in a very haphazard
manner.

As of version ``2.0.0-pre`` the command line interface is implemented using :mod:`argparse`
which allows for a cleaner separation of commands. Furthermore, the interaction with
the jira installation has been re-written so that a factory can be used to load the
appropriate bridge - thus supporting both the legacy ``soap rpc``
and the new ``json rest`` interfaces.




