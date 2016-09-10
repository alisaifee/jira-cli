"""

"""
import abc
import re
import requests
from requests import RequestException
import six
from six.moves.urllib import parse
from jiracli.cli import colorfunc
from jiracli.utils import COLOR


@six.add_metaclass(abc.ABCMeta)
class JiraBridge(object):

    def __init__(self, base_url, config, persist=True):
        self.base_url = self._check_redirect(base_url)
        self.config = config
        self.persist = persist

    def _check_redirect(self, url):
        try:
            resp = requests.get( url, allow_redirects = False )
            if resp.status_code in [301,302]:
                return resp.headers['location']
        except RequestException:
            return None
        finally:
            return url

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.base_url)

    def format_issue(self, issue, mode=0, formatter=None, comments_only=False):
        fields = {}
        status_color = "blue"
        status_string = JiraBridge.object_from_key(
            issue.setdefault('status', '1'),
            self.get_statuses
        )["name"]

        if status_string.lower() in ["resolved", "closed", "done"]:
            status_color = "green"
        elif status_string.lower() in ["open", "unassigned", "reopened", "to do"]:
            status_color = "red"

        special_fields = {
            "status": self.get_statuses,
            "priority": self.get_priorities,
            "type": lambda: dict(self.get_issue_types().items() + self.get_subtask_issue_types().items())
        }

        if formatter:
            groups = re.compile("(%([\w]+))").findall(formatter)
            ret_str = formatter.encode('utf-8')
            for k, v in groups:
                if v.lower() in special_fields.keys():
                    key=issue[v.lower()]
                    data = "" or JiraBridge.object_from_key(key, special_fields[v.lower()])["name"]
                    ret_str = ret_str.replace(k, data)
                else:
                    ret_str = ret_str.replace(k, issue.setdefault(v.lower(),"")).encode('utf-8')
            return ret_str
        if mode >= 0:
            # minimal
            fields["issue"] = issue["key"]
            fields["status"] = colorfunc(JiraBridge.object_from_key(issue["status"], self.get_statuses)["name"], status_color)
            fields["reporter"] = issue.setdefault("reporter","")
            fields["assignee"] = issue.setdefault("assignee","")
            fields["summary"] = issue.setdefault("summary","")
            fields["link"] = colorfunc(
                "%s/browse/%s" % (
                    self.base_url, issue["key"]
                ), "white", attrs=["underline"]
            )
        if mode == 1 or comments_only:
            fields["description"] = issue.setdefault("description","") or ""
            if not issue.get("priority", ""):
                self.fields["priority"] = ""
            else:
                fields["priority"] = JiraBridge.object_from_key(issue["priority"], self.get_priorities)["name"]
            fields["type"] = JiraBridge.object_from_key(
                issue["type"],
                self.get_issue_types if 'parent' not in issue else self.get_subtask_issue_types
            )["name"]
            fields["comments"] = "\n"
            comments = self.get_issue_comments(issue["key"])
            for comment in comments:
                comment_str =  comment["body"].strip()
                fields["comments"] += "%s %s : %s\n" % ( colorfunc(comment["created"], "blue"), colorfunc(comment["author"], "green"), comment_str )
        children_string = ""
        if mode > 1:
            description = (issue.setdefault("description", "") or "").split("\n")
            fields["description"] = "\n".join([description[0]] + [" "*23 + k for k in description[1:]])


            for child in self.search_issues_jql("parent=%s" % issue["key"]):
                child_type = JiraBridge.object_from_key(child["type"], self.get_subtask_issue_types)["name"].lower()
                key = ("%s" % child_type).ljust(20)
                value = "%s (%s) %s" % (
                    child["key"], child["summary"], colorfunc("%s/browse/%s" % (self.base_url, child["key"]), "white", attrs=['underline'])
                )
                children_string += "%s : %s\n" % (key, value)
        if comments_only:
            return fields["comments"].strip()
        elif mode < 0:
            url_str = colorfunc(parse.urljoin(self.base_url, "/browse/%s" % (issue["key"])), "white", attrs=["underline"])
            ret_str = colorfunc(issue["key"], status_color) + " " + issue.setdefault("summary", "") + " " + url_str
            if not COLOR:
                ret_str += " [%s] " % status_string
            return ret_str
        for k, v in fields.items():
            if not v:
                fields[k] = ""
        formatted = "\n".join(" : ".join((k.ljust(20), v)) for k, v in fields.items() if not k == 'comments') + "\n"
        formatted += children_string
        if "comments" in fields:
            formatted += fields["comments"]
        return formatted

    @staticmethod
    def object_from_key(value, callable, key='id'):
        map = callable()
        for k,v in map.items():
            if v[key] == value:
                return v
        return None

    @abc.abstractmethod
    def login(self, username, password):
        raise NotImplementedError

    @abc.abstractmethod
    def ping(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_filters(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_projects(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_components(self, project):
        raise NotImplementedError

    @abc.abstractmethod
    def list_versions(self, project):
        raise NotImplementedError

    @abc.abstractmethod
    def get_priorities(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_issue_types(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_subtask_issue_types(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_statuses(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_resolutions(self):
        raise NotImplementedError

    @abc.abstractmethod
    def get_issue(self, issue_id):
        raise NotImplementedError

    @abc.abstractmethod
    def update_issue(self, issue_id, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def search_issues(self, free_text, project=None, limit=100):
        raise NotImplementedError

    @abc.abstractmethod
    def search_issues_jql(self, query, limit=100, project=None):
        raise NotImplementedError

    @abc.abstractmethod
    def get_issues_by_filter(self, *filters):
        raise NotImplementedError

    @abc.abstractmethod
    def get_issue_comments(self, issue):
        raise NotImplementedError

    @abc.abstractmethod
    def add_comment(self, issue, comment):
        raise NotImplementedError

    @abc.abstractmethod
    def create_issue(
        self, project, type=0, summary="", description="", priority="minor", parent=None, components={}, **extras
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def get_available_transitions(self, issue):
        raise NotImplementedError

    @abc.abstractmethod
    def transition_issue(self, issue, transition, comment=""):
        raise NotImplementedError

    @abc.abstractmethod
    def assign_issue(self, issue, assignee):
        raise NotImplementedError

    @abc.abstractmethod
    def change_reporter(self, issue, reporter):
        raise NotImplementedError

    @abc.abstractmethod
    def add_versions(self, issue, versions, type):
        raise NotImplementedError

    @abc.abstractmethod
    def remove_versions(self, issue, versions, type):
        raise NotImplementedError

from .rest import JiraRestBridge
from .soap import JiraSoapBridge

def get_bridge(protocol):
    """
    simple factory to get the jira bridge based on the protocol
    """
    return {
        'soap': JiraSoapBridge,
        'rest': JiraRestBridge
    }[protocol]