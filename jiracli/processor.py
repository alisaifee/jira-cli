"""

"""
from abc import ABCMeta, abstractmethod
import argparse
from suds import WebFault
from jiracli.cli import colorfunc

import six

from jiracli.errors import UsageError, JiraError, UsageWarning
from jiracli.interface import initialize
from jiracli.utils import Config, print_error, WARNING, get_text_from_editor


@six.add_metaclass(ABCMeta)
class Command(object):
    def __init__(self, jira, args):
        self.args = args
        self.jira = jira
    @abstractmethod
    def eval(self):
        raise NotImplementedError


class ViewCommand(Command):
    def eval(self):
        if self.args.oneline:
            mode = -1
        elif self.args.verbosity > 1:
            mode = self.args.verbosity
        else:
            mode = 0
        if self.args.search_freetext:
            issues = self.jira.search_issues(self.args.search_freetext, project = self.args.project)
        elif self.args.search_jql:
            issues = self.jira.search_issues_jql(self.args.search_jql)
        else:
            issues = filter(lambda issue:issue is not None, [self.jira.get_issue(jira) for jira in self.args.jira_ids[0]])

        for issue in issues:
            print(self.jira.format_issue(
                issue,
                mode=mode,
                formatter=self.args.format,
                comments_only=self.args.comments_only
            ))

class ListCommand(Command):
    def eval(self):
        mappers = {
            "issue_types": (self.jira.get_issue_types,),
            'subtask_types': (self.jira.get_subtask_issue_types,),
            'projects': (self.jira.get_projects,),
            'priorities': (self.jira.get_priorities,),
            'statuses': (self.jira.get_statuses,),
            'resolutions': (self.jira.get_resolutions,),
            'components': (self.jira.get_components, 'project'),
            'transitions': (self.jira.get_available_transitions, 'issue'),
            'filters': (self.jira.get_filters,)
        }
        func, arguments = mappers[self.args.type][0], mappers[self.args.type][1:]
        _ = []
        for k in arguments:
            _.append(getattr(self.args, k))
        found = False

        for item in func(*_):
            found = True
            if type(item) == type({}):
                val = colorfunc(item['name'], 'white')
                if 'key' in item and item['key']:
                    val += "(" + colorfunc(item['key'], 'yellow') + ")"
                if 'description' in item and item['description']:
                    val += ":" + colorfunc(item['description'], 'green')
                print val
            else:
                print colorfunc(item, 'white')
        if not found:
            raise UsageWarning("No %s found." % self.args.type)

class UpdateCommand(Command):
    def eval(self):
        if self.args.issue_comment:
            self.jira.add_comment(self.args.issue, get_text_from_editor())
        elif self.args.issue_priority:
            self.jira.update_issue(
                self.args.issue,
                priority=self.jira.get_priorities()[self.args.issue_priority]["id"]
            )
        elif self.args.issue_components:
            components = dict(
                (k["name"], k["id"]) for k in self.jira.get_components(
                    self.args.issue.split("-")[0]
                )
            )
            current_components = set(k["name"] for k in self.jira.get_issue(self.args.issue)["components"])
            if not set(self.args.issue_components).issubset(current_components):
                new_components = current_components.union(self.args.issue_components)
                self.jira.update_issue(self.args.issue,
                                       components=[components[k] for k in new_components]
                )
                print colorfunc(
                    'component(s): %s added to %s' % (
                        ",".join(self.args.issue_components), self.args.issue), 'green'
                )
            else:
                raise UsageWarning("component(s):[%s] already exist in %s" % (
                    ",".join(self.args.issue_components), self.args.issue)
                )
        elif self.args.issue_transition:
            self.jira.transition_issue(self.args.issue, self.args.issue_transition)
            print colorfunc(
                '%s transitioned to "%s"' % (self.args.issue, self.args.issue_transition), 'green'
            )
class AddCommand(Command):
    def eval(self):
        if not self.args.issue_project:
            raise UsageError('project must be specified when creating an issue')
        if not (self.args.issue_parent or self.args.issue_type):
            self.args.issue_type = 'bug'
        if self.args.issue_type and not self.args.issue_type in self.jira.get_issue_types().keys() + self.jira.get_subtask_issue_types().keys():
            raise UsageError(
                "invalid issue type: %s (try using jira-cli "
                "list issue_types or jira-cli list subtask_types)" % self.args.issue_type
            )
        if self.args.issue_parent:
            if not self.args.issue_type:
                self.args.issue_type = 'sub-task'
            if not self.args.issue_type in self.jira.get_subtask_issue_types():
                raise UsageError(
                    "issues created with parents must be one of {%s}" % ",".join(self.jira.get_subtask_issue_types())
                )
        description = self.args.issue_description or get_text_from_editor()
        print(self.jira.format_issue(
            self.jira.create_issue(self.args.issue_project, self.args.issue_type, self.args.title, description,
                               self.args.issue_priority, self.args.issue_parent)
        ))


def build_parser():
    parser = argparse.ArgumentParser(description='jira-cli')

    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='additional help')
    view = subparsers.add_parser('view')
    view.set_defaults(cmd=ViewCommand)
    add = subparsers.add_parser('new')
    add.set_defaults(cmd=AddCommand)
    update = subparsers.add_parser('update')
    update.set_defaults(cmd=UpdateCommand)
    list = subparsers.add_parser('list')
    list.set_defaults(cmd=ListCommand)
    search_args = view.add_mutually_exclusive_group(required=False)

    search_args.add_argument('--search', dest='search_freetext')
    search_args.add_argument('--search-jql', dest='search_jql',
                             help='search using JQL')
    search_args.add_argument('--filter', dest='filter', help='filter(s) to use',
                             action='append')
    view.add_argument('--project', help='the jira project to act on',
                      dest='project')
    view.add_argument('--comments-only', dest='comments_only',
                      help='displays only the comments assosciated with each issue',
                      action='store_true')
    view.add_argument('jira_ids', type=str, nargs='*', action='append')

    parser.add_argument('-u', '--username', dest='username',
                        help='username to login as', default=None)
    parser.add_argument('-p', '--password', dest='password',
                        help='password for jira instance', default=None)
    parser.add_argument('--jira-url', dest='jira_url',
                        help='the base url for the jira instance', default=None)
    parser.add_argument("--format", dest="format", default=None,
                        help=r'format for displaying ticket information. '
                             r'allowed tokens: status,priority,updated,votes,'
                             r'components,project,reporter,created,fixVersions,'
                             r'summary,environment,assignee,key,'
                             r'affectsVersions,type.'
                             r'Use the %% character before each token '
                             r'(example: issue id: %%key [%%priority])')
    parser.add_argument('--oneline', dest='oneline',
                        help='built in format to display each ticket on one line',
                        action='store_true')
    parser.add_argument('-v', dest='verbosity', help='amount of detail to show',
                        action='count')
    list.add_argument('type', choices=['filters', 'projects', 'issue_types',
                                       'subtask_types', 'priorities',
                                       'statuses', 'components', 'resolutions',
                                       'transitions'])
    list.add_argument('--project', help='the jira project to act on',
                      dest='project')
    list.add_argument('--issue', help='the jira issue to act on',
                      dest='issue')

    add.add_argument('title', help='new issue title', nargs='+')
    add.add_argument('--priority', dest='issue_priority',
                     help='new issue priority', default='minor')
    add.add_argument('--project', dest='issue_project',
                     help='project to create new issue in')
    add.add_argument('--description', dest='issue_description',
                     help='description of new issue')
    add.add_argument('--type', dest='issue_type', help='new issue priority')
    add.add_argument('--parent', dest='issue_parent',
                     help='parent of new issue')

    update.add_argument('issue', help='the jira issue to act on')
    update.add_argument('--comment', dest='issue_comment',
                        action='store_true', help='add a comment to an existing issue')
    update.add_argument('--priority', '--priority', dest='issue_priority',
                        help='change the priority of an issue')
    update.add_argument('--component', dest='issue_components',
                        action='append', help='add components(s) to an issue'
                                              ' (use list components to view available components)')
    update.add_argument('--transition', dest='issue_transition',
                        help='transition the issue to a new state'
                             ' (use list transitions to view available transitions for an issue)')
    return parser


def cli():
    parser = build_parser()
    args = parser.parse_args()
    config = Config()
    try:
        jira = initialize(
            config, args.jira_url, args.username, args.password,
            persist=not (args.username or args.jira_url)
        )
        args.cmd(jira, args).eval()
    except KeyboardInterrupt:
        print_error("aborted", severity=WARNING)
    except UsageWarning, e:
        print_error(str(e), severity=WARNING)
    except (JiraError, UsageError), e:
        print_error(str(e))
    except (WebFault), e:
        print_error(JiraError(e))

if __name__ == "__main__":
    cli()

