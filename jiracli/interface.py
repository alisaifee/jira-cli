"""

"""
import getpass
from jiracli.bridges import JiraSoapBridge
from jiracli.errors import JiraAuthenticationError, JiraInitializationError
from jiracli.utils import print_error, WARNING


def initialize(config, base_url=None, username=None, password=None, persist=True):
    url = base_url or config.base_url
    bridge = JiraSoapBridge(url, config, persist)
    if not (url and bridge.ping()):
        url = url or raw_input("Base url for the jira instance: ")
        username = username or raw_input("username: ")
        password = password or getpass.getpass("password: ")
        jira = JiraSoapBridge(url, config, persist)
        if persist:
            config.add_option('base_url', url)
        try:
            jira.login(username, password)
            config.save()
            return jira
        except JiraAuthenticationError:
            print_error("invalid username/password", severity=WARNING)
            return initialize(config, base_url=url)
        except JiraInitializationError:
            print_error("invalid jira location", severity=WARNING)
            return initialize(config)
    else:
        return bridge