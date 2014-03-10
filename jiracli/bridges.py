"""

"""
import re
import socket
import urllib2
import abc

import six
from suds.client import Client
from suds import WebFault

from jiracli.cache import cached
from jiracli.cli import colorfunc
from jiracli.errors import JiraInitializationError, JiraAuthenticationError, JiraError
from jiracli.utils import soap_recursive_dict, COLOR


@six.add_metaclass(abc.ABCMeta)
class JiraBridge(object):

    def __init__(self, base_url, config):
        self.base_url = base_url
        self.config = config


    def format_issue( self, issue , mode = 0, formatter=None, comments_only=False):
        fields = {}
        status_color = "blue"
        status_string = self.object_from_id(
            issue.setdefault('status', '1'),
            self.get_statuses
        )["name"].lower()

        if status_string in ["resolved", "closed", "done"]:
            status_color = "green"
        elif status_string in ["open", "unassigned", "reopened", "to do"]:
            status_color = "red"

        special_fields = {
            "status": self.get_statuses,
            "priority": self.get_priorities,
            "type": self.get_issue_types
        }

        if formatter:
            groups = re.compile("(%([\w]+))").findall(formatter)
            ret_str = formatter
            for k, v in groups:
                if v.lower() in special_fields.keys():
                    key=issue[v.lower()]
                    data = "" or self.object_from_id(key, special_fields[v.lower()])["name"]
                    ret_str = ret_str.replace(k, data)
                else:
                    ret_str = ret_str.replace(k, str(issue.setdefault(v.lower(),"")))
            return ret_str

        if mode >= 0:
            # minimal
            fields["issue"] = issue["key"]
            fields["status"] = colorfunc(self.object_from_id(issue["status"], self.get_statuses)["name"], status_color)
            fields["reporter"] = issue.setdefault("reporter","")
            fields["assignee"] = issue.setdefault("assignee","")
            fields["summary"] = issue.setdefault("summary","")
            fields["link"] = colorfunc( "%s/browse/%s" % ( self.base_url, issue["key"]), "white",attrs=["underline"])
        if mode == 1 or comments_only:
            fields["description"] = issue.setdefault("description","")
            if not issue.get("priority", ""):
                self.fields["priority"] = ""
            else:
                fields["priority"] = self.object_from_id(issue["priority"], self.get_priorities)["name"]
            fields["type"] = self.object_from_id(issue["type"], self.get_issue_types)["name"]
        children_string = ""
        if mode > 1:
            comments = self.get_issue_comments(issue["key"])
            description = issue.setdefault("description", "").split("\n")
            fields["description"] = "\n".join([description[0]] + [" "*23 + k for k in description[1:]])

            fields["comments"] = "\n"
            for comment in comments:
                comment_str =  comment["body"].strip()
                fields["comments"] += "%s %s : %s\n" % ( colorfunc(comment["created"], "blue"), colorfunc(comment["author"], "green"), comment_str )

            for child in self.search_issues_jql("parent=%s" % issue["key"]):
                child_type = self.object_from_id(child["type"], self.get_subtask_issue_types)["name"].lower()
                key = ("%s" % child_type).ljust(20)
                value = "%s (%s) %s" % (
                    child["key"], child["summary"], colorfunc("%s/browse/%s" % (self.base_url, child["key"]), "white", attrs=['underline'])
                )
                children_string += "%s : %s\n" % (key, value)
        if comments_only:
            return fields["comments"].strip()
        elif mode < 0:
            url_str = colorfunc("%s/browse/%s" % (self.base_url, issue["key"]), "white", attrs=["underline"])
            ret_str = colorfunc(issue["key"], status_color) + " " + issue.setdefault("summary", "") + " " + url_str
            if not COLOR:
                ret_str += " [%s] " % self.get_statuses()[issue["status"]]
            return ret_str
        for k, v in fields.items():
            if not v:
                fields[k] = ""
        formatted = "\n".join(" : ".join((k.ljust(20), v)) for k, v in fields.items() if not k == 'comments') + "\n"
        formatted += children_string
        if "comments" in fields:
            formatted += fields["comments"]
        return formatted

    @abc.abstractmethod
    def login(self, username, password):
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

    def object_from_id(self, id, callable):
        map = callable()
        for k,v in map.items():
            if v["id"] == id:
                return v
        return None

    @abc.abstractmethod
    def get_issue(self, issue_id):
        raise NotImplementedError

    @abc.abstractmethod
    def get_children(self, issue_id):
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
    def create_issue(self, project, type=0, summary="", description="", priority="minor", parent=None):
        raise NotImplementedError

    @abc.abstractmethod
    def get_available_transitions(self, issue):
        raise NotImplementedError

    @abc.abstractmethod
    def transition_issue(self, issue, transition, comment=""):
        raise NotImplementedError
    @abc.abstractmethod
    def ping(self):
        raise NotImplementedError


class JiraSoapBridge(JiraBridge):

    def get_children(self, issue_id):
        return [soap_recursive_dict(item) for item in self.service.getSubTasks(self.token, issue_id)]

    @cached("subtasks_issue_types")
    def get_subtask_issue_types(self):
        issue_types = self.service.getSubTaskIssueTypes(self.token)
        issue_types = [soap_recursive_dict(k) for k in issue_types]
        return dict((item['name'].lower(), item) for item in issue_types)


    def ping(self):
        if type(self.service) == type(None):
            return False
        try:
            self.service.getIssueTypes(self.token)
            return True
        except WebFault:
            return False

    def __init__(self, base_url, config, persist=True):
        super(JiraSoapBridge, self).__init__(base_url, config)
        self.persist = persist
        try:
            urllib2.urlopen('%s/rpc/soap/jirasoapservice-v2?wsdl' % self.base_url)
            jiraobj = Client('%s/rpc/soap/jirasoapservice-v2?wsdl' % self.base_url)
            self.service = jiraobj.service
        except (socket.gaierror, IOError, ValueError):
            self.service = None
        self.token = config.token
    def transition_issue(self, issue, transition, comment=""):
        transitions = self.get_available_transitions(issue)
        try:
            return self.service.progressWorkflowAction(self.token, issue, transitions[transition])
        except KeyError:
            raise JiraError("Invalid transition '%s'. Use one of [%s]" % (transition, ",".join(transitions)))

    def get_available_transitions(self, issue):
        transitions = self.service.getAvailableActions(self.token, issue)
        if not transitions:
            raise JiraError("No transitions found for issue %s" % issue)
        return dict((k.name.lower(), k.id) for k in transitions)

    def create_issue(self, project, type='bug', summary="", description="", priority="minor", parent=None):
        issue = {
            "project": project.upper(),
            "summary": summary,
            "description": description,
            "priority": self.get_priorities()[priority.lower()]["id"]
        }
        try:
            if parent:
                issue['type'] = self.get_subtask_issue_types()[type.lower()]['id'],
                return soap_recursive_dict(self.service.createIssueWithParent(self.token, issue, parent))
            else:
                issue['type'] = self.get_issue_types()[type.lower()]['id'],
                return soap_recursive_dict(self.service.createIssue(self.token, issue))
        except WebFault, e:
            raise JiraError(e)

    def get_issue_comments(self, issue):
        return [soap_recursive_dict(k) for k in self.service.getComments(self.token, issue)]

    def add_comment(self, issue, comment):
        return self.service.addComment(self.token, issue, {'body':comment})


    def update_issue(self, issue_id, **kwargs):
        mapped = [{"id":k, "values":[kwargs[k]]} for k in kwargs]
        return self.service.updateIssue(self.token, issue_id, mapped)

    @cached('filters')
    def get_filters(self):
        filters = self.service.getSavedFilters(self.token)
        filters += self.service.getFavouriteFilters(self.token)
        return dict((item["name"].lower(), soap_recursive_dict(item)) for item in filters)

    @cached('priorities')
    def get_priorities(self):
        priorities = [soap_recursive_dict(k) for k in self.service.getPriorities(self.token)]
        return dict((item["name"].lower(), item) for item in priorities)

    @cached('issue_types')
    def get_issue_types(self):
        issue_types = self.service.getIssueTypes(self.token)
        issue_types = [soap_recursive_dict(k) for k in issue_types]
        return dict((item['name'].lower(), item) for item in issue_types)

    @cached('projects')
    def get_projects(self):
        return [soap_recursive_dict(k) for k in self.service.getProjectsNoSchemes(self.token)]

    def get_components(self, project):
        return [soap_recursive_dict(k) for k in self.service.getComponents(self.token, project)]

    def login(self, username, password):
        if type(self.service) == type(None):
            raise JiraInitializationError()
        try:
            if not (self.token and self.ping()):
                self.token = self.service.login(username, password)
        except (WebFault, AttributeError):
            self.token = None
            raise JiraAuthenticationError()
        finally:
            print self.persist
            if self.persist:
                self.config.add_option('token', self.token)
                self.config.save()

    @cached('status')
    def get_statuses(self):
        statuses = [soap_recursive_dict(k) for k in self.service.getStatuses(self.token)]
        return dict((item['name'].lower(), item) for item in statuses)

    def search_issues_jql(self, query, limit=100):
        return [soap_recursive_dict(k) for k in self.service.getIssuesFromJqlSearch(self.token, query, limit)]

    def search_issues(self, free_text, project=None, limit = 100):
        if not project:
            return [soap_recursive_dict(k) for k in self.service.getIssuesFromTextSearch(self.token, free_text)]
        else:
            return [soap_recursive_dict(k) for k in self.service.getIssuesFromTextSearchWithProject(self.token, [project], free_text, limit)]

    def get_issue(self, issue_id):
        try:
            return soap_recursive_dict(self.service.getIssue( self.token, issue_id))
        except WebFault:
            return None

    def get_issues_by_filter(self, *filters):
        issues = []
        for filter in filters:
            fid = self.get_filters()[filter]["id"]
            if fid:
                return issues.extend(self.service.getIssuesFromFilter(self.token, fid))
        return [soap_recursive_dict(k) for k in issues]

    @cached('resolutions')
    def get_resolutions(self):
        resolutions = [soap_recursive_dict(k) for k in self.service.getResolutions(self.token)]
        return dict((item['name'], item) for item in resolutions)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.base_url)



