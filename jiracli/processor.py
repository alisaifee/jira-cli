"""

"""
from abc import ABCMeta, abstractmethod

import six

from jiracli.cli import colorfunc
from jiracli.errors import UsageError, UsageWarning
from jiracli.utils import get_text_from_editor


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
            if not getattr(self.args, k):
                raise UsageError("'%s' is required for listing '%s'" % (k, self.args.type))
            _.append(getattr(self.args, k))
        found = False

        for item in func(*_):
            found = True
            if type(item) == type({}):
                val = colorfunc(item['name'], 'white')
                if 'key' in item and item['key']:
                    val += " [" + colorfunc(item['key'], 'magenta') + "]"
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
        elif self.args.issue_assignee:
            self.jira.update_issue(self.args.issue, assignee=self.args.issue_assignee)
            print colorfunc(
                '%s assigned to %s' % (self.args.issue, self.args.issue_assignee), 'green'
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







