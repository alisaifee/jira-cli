"""

"""
import re
import socket
import abc

from jira.exceptions import JIRAError
from jira.resources import Resource
import requests
from requests.exceptions import RequestException
import six
from six.moves.urllib import parse, request
from suds.client import Client
from suds import WebFault
from jira.client import JIRA

from jiracli.cache import cached
from jiracli.cli import colorfunc
from jiracli.errors import JiraInitializationError, JiraAuthenticationError, JiraCliError
from jiracli.utils import soap_recursive_dict, COLOR, map_rest_resource
from jiracli.utils import rest_recursive_dict


def get_bridge(protocol):
    """
    simple factory to get the jira bridge based on the protocol
    """
    return {
        'soap': JiraSoapBridge,
        'rest': JiraRestBridge
    }[protocol]

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
                    data = "" or JiraBridge.object_from_key(key, special_fields[v.lower()])["name"]
                    ret_str = ret_str.replace(k, data)
                else:
                    ret_str = ret_str.replace(k, str(issue.setdefault(v.lower(),"")))
            return ret_str

        if mode >= 0:
            # minimal
            fields["issue"] = issue["key"]
            fields["status"] = colorfunc(JiraBridge.object_from_key(issue["status"], self.get_statuses)["name"], status_color)
            fields["reporter"] = issue.setdefault("reporter","")
            fields["assignee"] = issue.setdefault("assignee","")
            fields["summary"] = issue.setdefault("summary","")
            fields["link"] = colorfunc( parse.urljoin(self.base_url, "/browse/%s" % (issue["key"])), "white",attrs=["underline"])
        if mode == 1 or comments_only:
            fields["description"] = issue.setdefault("description","") or ""
            if not issue.get("priority", ""):
                self.fields["priority"] = ""
            else:
                fields["priority"] = JiraBridge.object_from_key(issue["priority"], self.get_priorities)["name"]
            fields["type"] = JiraBridge.object_from_key(issue["type"], self.get_issue_types)["name"]
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
    def create_issue(self, project, type=0, summary="", description="", priority="minor", parent=None):
        raise NotImplementedError

    @abc.abstractmethod
    def get_available_transitions(self, issue):
        raise NotImplementedError

    @abc.abstractmethod
    def transition_issue(self, issue, transition, comment=""):
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
            self.token = self.config.token = None
            self.config.save()
            return False

    def __init__(self, base_url, config, persist=True):
        super(JiraSoapBridge, self).__init__(base_url, config, persist)
        try:
            request.urlopen('%s/rpc/soap/jirasoapservice-v2?wsdl' % self.base_url)
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
            raise JiraCliError("Invalid transition '%s'. Use one of [%s]" % (transition, ",".join(transitions)))

    def get_available_transitions(self, issue):
        transitions = self.service.getAvailableActions(self.token, issue)
        if not transitions:
            raise JiraCliError("No transitions found for issue %s" % issue)
        return dict((k.name.lower(), k.id) for k in transitions)

    def create_issue(self, project, type='bug', summary="", description="", priority="minor", parent=None):
        issue = {
            "project": project.upper(),
            "summary": summary,
            "description": description,
            "priority": self.get_priorities()[priority.lower()]["id"]
        }
        if type == 'epic':
            issue['customfield_11401'] = summary
        try:
            if parent:
                issue['type'] = self.get_subtask_issue_types()[type.lower()]['id'],
                return soap_recursive_dict(self.service.createIssueWithParent(self.token, issue, parent))
            else:
                issue['type'] = self.get_issue_types()[type.lower()]['id'],
                return soap_recursive_dict(self.service.createIssue(self.token, issue))
        except WebFault as e:
            raise JiraCliError(e)

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
                self.token = self.config.token = self.service.login(username, password)
        except (WebFault, AttributeError):
            self.token = None
            raise JiraAuthenticationError()
        finally:
            if self.persist:
                self.config.token = self.token
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




class JiraRestBridge(JiraBridge):
    def __init__(self, base_url, config, persist=False):
        super(JiraRestBridge, self).__init__(base_url, config, persist)
        self.jira = None

    @cached('resolutions')
    def get_resolutions(self):
        return dict((r.name, rest_recursive_dict(r.raw)) for r in self.jira.resolutions())

    @cached('filters')
    def get_filters(self):
        filters = dict((f.name, rest_recursive_dict(f.raw)) for f in self.jira.favourite_filters())
        return filters

    def clean_issue(self, issue):
        _issue = {}
        for k,v in issue.fields.__dict__.items():
            if isinstance(v, Resource):
                _issue[k] = map_rest_resource(v)
            elif v is not None:
                _issue[k] = v
        _issue['key'] = issue.key
        _issue['type'] = map_rest_resource(_issue['issuetype'])
        return _issue

    def get_issue(self, issue_id):
        try:
            return self.clean_issue(self.jira.issue(issue_id))
        except:
            return None

    def search_issues(self, free_text, project=None, limit=100):
        query = '(summary~"%s" or description~"%s")' % (free_text, free_text)
        if project:
            query += ' and project=%s' % project
        query += ' order by key'
        return [self.clean_issue(issue) for issue in self.jira.search_issues(query,maxResults=100)]

    def search_issues_jql(self, query, limit=100, project=None):
        return [self.clean_issue(issue) for issue in self.jira.search_issues(query, maxResults=100)]

    def get_issues_by_filter(self, *filters):
        issues = []
        for filter in filters:
            issues.extend([issue for issue in self.search_issues_jql('filter=%s' % filter)])
        return issues

    def add_comment(self, issue, comment):
        self.jira.add_comment(issue, comment)


    def transition_issue(self, issue, transition, comment=""):
        transitions = self.get_available_transitions(issue)
        try:
            return self.jira.transition_issue(issue, transitions[transition]['id'])
        except KeyError:
            raise JiraCliError("Invalid transition '%s'. Use one of [%s]" % (transition, ",".join(transitions)))

    def ping(self):
        return False

    def create_issue(self, project, type='bug', summary="", description="", priority="minor", parent=None):
        issue = {
            "project": {'key':project.upper()},
            "summary": summary,
            "description": description,
            "priority": {'id':self.get_priorities()[priority.lower()]["id"]}
        }
        if type == 'epic':
            issue['customfield_11401'] = summary
        if parent:
            issue['issuetype'] = {'id':self.get_subtask_issue_types()[type.lower()]['id']}
            issue['parent'] = {'key':parent}
        else:
            issue['issuetype'] = {'id':self.get_issue_types()[type.lower()]['id']}
        return self.clean_issue(self.jira.create_issue(issue))

    def login(self, username, password):
        try:
            self.jira = JIRA(options={'server': self.base_url},
                         basic_auth=(username, password), validate=True
            )
        except JIRAError:
            raise JiraAuthenticationError('failure to authenticate')
        except RequestException:
            raise JiraInitializationError('failure to communicate with jira')

    def get_available_transitions(self, issue):
        return dict((t['name'].lower(), t) for t in self.jira.transitions(issue))

    @cached('issue_types')
    def get_issue_types(self):
        types = dict((k.name.lower(), k.raw) for k in self.jira.issue_types() if not k.subtask)
        for k in types:
            if k=='id':
                types['id'] = types['id'][0]
        return types

    @cached('subtask_types')
    def get_subtask_issue_types(self):
        types = dict((k.name.lower(), k.raw) for k in self.jira.issue_types() if k.subtask)
        for k in types:
            if k=='id':
                types['id'] = types['id'][0]
        return types

    def update_issue(self, issue_id, **kwargs):
        pass

    @cached('projects')
    def get_projects(self):
        return dict((k.name.lower(), k.raw) for k in self.jira.projects())

    @cached('priorities')
    def get_priorities(self):
        return dict((k.name.lower(), dict(k.raw)) for k in self.jira.priorities())

    @cached('components')
    def get_components(self, project):
        return dict((k.name.lower(), dict(k.raw)) for k in self.jira.project_components(project))

    @cached('statuses')
    def get_statuses(self):
        return dict((k.name.lower(), dict(k.raw)) for k in self.jira.statuses())

    def get_issue_comments(self, issue):
        return [
            dict(author=comment.author.name
                 , body=comment.body
                 , created=comment.created
            )
            for comment in self.jira.comments(issue)
        ]
