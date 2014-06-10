from jira.exceptions import JIRAError
from suds import WebFault


class JiraInitializationError(Exception):
    pass


class JiraAuthenticationError(Exception):
    pass


class UsageError(Exception):
    pass

class UsageWarning(Exception):
    pass


class JiraCliError(Exception):
    def __init__(self, exc):
        if isinstance(exc, WebFault):
            msg = ":".join(exc.fault.faultstring.split(":")[1:]).strip()
            super(JiraCliError, self).__init__(msg)
        elif isinstance(exc, JIRAError):
            super(JiraCliError, self).__init__(exc.text)
        else:
            super(JiraCliError, self).__init__(exc)

