Introduction
============
Simple command line utility to interact with your jira instance. 

.. image:: https://api.travis-ci.org/alisaifee/jira-cli.png
   :alt: build status

Installation
============
* with easy_install or pip::
   
    sudo easy_install jira-cli
    sudo pip install jira-cli

* from source:: 

    hg clone http://github.com/alisaifee/jira-cli
    cd jira-cli
    python setup.py build
    sudo python setup.py install

* after installation, a few configuration steps will be prompted upon invoking jira-cli for the first time::
    
    ali@home ~ $ jira-cli
    base url for your jira instance (e.g http://issues.apache.org/jira):http://jira.yourdomain.com
    enter username:ali
    enter password:*********

  The details of your jira instance will be kept in ~/.jira-cli/config and the authentication token will be stored in ~/.jira-cli/auth.
  Once the authentication token has expired you will be reprompted for your username & password again. Alternatively you can provide the username and password on the command line as::

    ali@home ~ $ jira-cli --user=ali --password=sekret ...

  

Usage
=====

A few examples to get started.
------------------------------
create an issue with only a title in project TP with default priority and type Bug::

    ali@home ~ $ jira-cli -n Bug -t "Test Bug" --priority=Major -p TP
    link                 : http://jira.yourdomain.com/browse/TP-24
    assignee             : 
    summary              : Test Bug
    issue                : TP-24
    reporter             : ali   
 
create an issue with priority Major and a description::
    
    ali@home ~ $ jira-cli -n Bug -t "Test Bug" --priority=Major -p TP the description
    link                 : http://jira.yourdomain.com/browse/TP-25
    assignee             : 
    summary              : Test Bug
    issue                : TP-25
    reporter             : ali

list the issue TP-25::
    
    ali@home ~ $ jira-cli TP-25
    link                 : http://jira.yourdomain.com/browse/TP-25
    assignee             : 
    summary              : Test Bug
    issue                : TP-25
    reporter             : ali


list the issues TP-20 & TP-21::
    
    ali@home ~ $ jira-cli TP-20 TP-21
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

    ali@home ~ $ jira-cli TP-20 TP-21 TP-22 --oneline
    TP-20 test < http://jira.yourdomain.com/browse/TP-20 > 
    TP-21 Test Bug < http://jira.yourdomain.com/browse/TP-21 > 
    TP-22 Test Bug < http://jira.yourdomain.com/browse/TP-22 > 

add a comment to an existing issue::
    
    ali@home ~ $ jira-cli -j TP-20 -c this is a new comment
    this is a new comment added to TP-20

provide your own formatting::

    ali@home ~ $ jira-cli TP-20 --format="%reporter, %summary, %status"

free text search for issues::
    
    ali@home ~ $ jira-cli --search some random words 


