"""

"""
import socket
from suds import WebFault
from suds.client import Client
from jiracli.bridge import JiraBridge
from jiracli.cache import cached
from jiracli.errors import JiraCliError, JiraInitializationError, \
    JiraAuthenticationError, UsageError
from jiracli.utils import soap_recursive_dict
from six.moves.urllib import request

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

    def transition_issue(self, issue, transition, resolution):
        transitions = self.get_available_transitions(issue)
        try:
            fields = {}
            if resolution:
                fields.append({"resolution": self.get_resolutions()[resolution]["id"]})
            return self.service.progressWorkflowAction(
                self.token, issue, transitions[transition]['id'], fields
            )
        except KeyError:
            raise JiraCliError("Invalid transition '%s'. Use one of [%s]" % (transition, ",".join(transitions)))

    def get_available_transitions(self, issue):
        transitions = self.service.getAvailableActions(self.token, issue)
        if not transitions:
            raise JiraCliError("No transitions found for issue %s" % issue)
        return dict((k.name.lower(), soap_recursive_dict(k)) for k in transitions)

    def create_issue(self, project, type='bug', summary="", description="",
                     priority="minor", parent=None, assignee="", reporter="",
                     labels=[], components={}, **extras):
        issue = {
            "project": project.upper(),
            "summary": summary,
            "description": description,
            "priority": self.get_priorities()[priority.lower()]["id"],
            "assignee": assignee,
            "reporter": reporter,
            "components": [{"name": k, "id": components[k]} for k in components]
        }
        if not issue["components"]:
            issue.pop("components")
        if type.lower() == 'epic':
            issue['customfield_11401'] = summary
        try:
            if parent:
                issue['type'] = self.get_subtask_issue_types()[type.lower()]['id'],
                created_issue = soap_recursive_dict(self.service.createIssueWithParent(self.token, issue, parent))
            else:
                issue['type'] = self.get_issue_types()[type.lower()]['id'],
                created_issue = soap_recursive_dict(self.service.createIssue(self.token, issue))
            if assignee or reporter or labels:
                if assignee:
                    created_issue = self.assign_issue(created_issue['key'], assignee)
                if reporter:
                    created_issue = self.change_reporter(created_issue['key'], reporter)
                if labels:
                    created_issue = self.add_labels(created_issue['key'], labels)
                return soap_recursive_dict(created_issue)
            else:
                return created_issue
        except WebFault as e:
            raise JiraCliError(e)

    def get_issue_comments(self, issue):
        return [soap_recursive_dict(k) for k in self.service.getComments(self.token, issue)]

    def add_comment(self, issue, comment):
        return self.service.addComment(self.token, issue, {'body':comment})

    def update_issue(self, issue_id, **kwargs):
        mapped = [{"id":k, "values":[kwargs[k]]} for k in kwargs]
        return self.service.updateIssue(self.token, issue_id, mapped)

    def assign_issue(self, issue_id, assignee):
        return self.update_issue(issue_id, assignee = assignee)

    def change_reporter(self, issue_id, reporter):
        return self.update_issue(issue_id, reporter = reporter)

    def add_labels(self, issue_id, labels, merge=False):
        if merge:
            raise JiraCliError("updating labels via the soap protocol is not supported")
        return self.update_issue(issue_id, labels=labels)

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

    def list_versions(self, project):
        return [soap_recursive_dict(k) for k in self.service.getVersions(self.token, project)]

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
            try:
                fid = self.get_filters()[filter]["id"]
                issues.extend(self.service.getIssuesFromFilter(self.token, fid))
            except KeyError:
                raise UsageError("filter %s not found" % filter)
        return [soap_recursive_dict(k) for k in issues]

    @cached('resolutions')
    def get_resolutions(self):
        resolutions = [soap_recursive_dict(k) for k in self.service.getResolutions(self.token)]
        return dict((item['name'], item) for item in resolutions)

    def get_versions(self, issue):
        project_key = issue.split("-")[0]
        versions = [soap_recursive_dict(k) for k in self.service.getVersions(self.token, project_key)]
        return dict((item['name'], item) for item in versions)

    def add_versions(self, issue, versions, type):
        project_versions = self.get_versions(issue)
        ids = []
        issue_obj = self.get_issue(issue)
        for version in versions:
            if version not in project_versions:
                raise UsageError("%s is not a valid version for issue %s" % (version, issue))
            ids.append(project_versions[version]['id'])
        [ids.append(v['id']) for v in issue_obj.get('fixVersions' if type == 'fix' else 'affectsVersions', [])]
        args = {}

        if type == 'fix':
            args = {'fixVersions': ids}
        elif type == 'affects':
            args = {'versions': ids}
        return self.update_issue(issue, **args)

    def remove_versions(self, issue, versions, type):
        issue_obj = self.get_issue(issue)
        current_versions = issue_obj.get('fixVersions' if type == 'fix' else 'affectsVersions', [])
        ids = []
        for version in list(current_versions):
            if version['name'] not in versions:
                ids.append(version['id'])
        args = {}
        if type == 'fix':
            args = {'fixVersions': ids}
        elif type == 'affects':
            args = {'versions': ids}
        self.update_issue(issue, **args)
