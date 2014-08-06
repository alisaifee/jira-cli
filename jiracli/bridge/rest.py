"""

"""
from jira.client import JIRA
from jira.exceptions import JIRAError
from jira.resources import Resource
from requests import RequestException
from jiracli.bridge import JiraBridge
from jiracli.cache import cached
from jiracli.errors import JiraCliError, JiraAuthenticationError, \
    JiraInitializationError
from jiracli.utils import rest_recursive_dict, map_rest_resource


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