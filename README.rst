Introduction
============
Simple command line utility to interact with your jira instance. 

.. |travis-ci| image:: https://api.travis-ci.org/alisaifee/jira-cli.png
   :alt: build status
   :target: https://travis-ci.org/#!/alisaifee/jira-cli
.. |coveralls| image:: https://coveralls.io/repos/alisaifee/jira-cli/badge.png?branch=rewrite
    :target: https://coveralls.io/r/alisaifee/jira-cli?branch=rewrite
.. |pypi| image:: https://pypip.in/v/jira-cli/badge.png
    :target: https://crate.io/packages/jira-cli/
.. |license| image:: https://pypip.in/license/jira-cli/badge.png
    :target: https://pypi.python.org/pypi/jira-cli/

|travis-ci| |coveralls| |pypi| |license|

Installation
============
* with easy_install or pip::
   
    sudo easy_install jira-cli
    sudo pip install jira-cli

* from source:: 

    git clone http://github.com/alisaifee/jira-cli
    cd jira-cli
    python setup.py build
    sudo python setup.py install

* after installation, a few configuration steps will be prompted upon invoking jira-cli for the first time::
    
    ali@home ~ $ jira-cli
    Base url for the jira instance: http://jira.yourdomain.com
    username:ali
    password:*********

  The details of your jira instance will be kept in ~/.jira-cli/config and the authentication token will be stored in ~/.jira-cli/auth.
  Once the authentication token has expired you will be reprompted for your username & password again. Alternatively you can provide the username and password on the command line as::

    ali@home ~ $ jira-cli --username=ali --password=sekret --jira-url=http://...

  

Usage
=====

A few examples to get started.
------------------------------
create an issue with only a title in project TP with default priority and type Bug::

    ali@home ~ $ jira-cli new --type=bug --priority=Major --project TP 'Test Bug'
    link                 : http://jira.yourdomain.com/browse/TP-24
    assignee             : 
    summary              : Test Bug
    issue                : TP-24
    reporter             : ali   
 
create an issue with priority Major and a description::
    
    ali@home ~ $ jira-cli --type Bug "Test Bug" --priority=Major --project TP --description='the description'
    link                 : http://jira.yourdomain.com/browse/TP-25
    assignee             : 
    summary              : Test Bug
    issue                : TP-25
    reporter             : ali

list the issue TP-25::
    
    ali@home ~ $ jira-cli view TP-25
    link                 : http://jira.yourdomain.com/browse/TP-25
    assignee             : 
    summary              : Test Bug
    issue                : TP-25
    reporter             : ali


list the issues TP-20 & TP-21::
    
    ali@home ~ $ jira-cli view TP-20 TP-21
    link                 : http://jira.yourdomain.com/browse/TP-20
    assignee             : ali
    summary              : test
    issue                : TP-20
    reporter             : ali

    link                 : http://jira.yourdomain.com/browse/TP-21
    assignee             : 
    summary              : Test Bug
    issue                : TP-21
    reporter             : ali

list the issues in short form::

    ali@home ~ $ jira-cli view TP-20 TP-21 TP-22 --oneline
    TP-20 test < http://jira.yourdomain.com/browse/TP-20 > 
    TP-21 Test Bug < http://jira.yourdomain.com/browse/TP-21 > 
    TP-22 Test Bug < http://jira.yourdomain.com/browse/TP-22 > 

add a comment to an existing issue::
    
    ali@home ~ $ jira-cli update TP-20 --comment # opens up the editor 
    this is a new comment added to TP-20

provide your own formatting::

    ali@home ~ $ jira-cli view TP-20 --format="%reporter, %summary, %status" 

free text search for issues::
    
    ali@home ~ $ jira-cli view --search='some random words' 

jql search for issues::
    
    ali@home ~ $ jira-cli view --search-jql 'reporter=ali and type=bug' 


list only the comments for an issue::

    ali@home ~ $ jira-cli view TP-20 --comments-only 
    Thu Nov 10 08:42:55 UTC 2011 ali : this is a new comment
    Fri Dec 02 00:19:40 UTC 2011 ali : another comment 
    Sat Mar 10 11:08:34 UTC 2012 ali : test comment
    Sat Mar 10 11:08:51 UTC 2012 ali : another test comment


