from suds import WebFault


class JiraInitializationError(Exception):
    pass


class JiraAuthenticationError(Exception):
    pass


class UsageError(Exception):
    pass
class UsageWarning(Exception):
    pass


class JiraError(Exception):
    def __init__(self, exc):
        if isinstance(exc, WebFault):
            msg = ":".join(exc.fault.faultstring.split(":")[1:]).strip()
            super(JiraError, self).__init__(msg)
        else:
            super(JiraError, self).__init__(exc)

