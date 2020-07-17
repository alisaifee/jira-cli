"""

"""
from __future__ import division
from __future__ import print_function
from builtins import str
from past.builtins import basestring
from past.utils import old_div
from builtins import object
import json
from abc import ABCMeta, abstractmethod

import six

from jiracli.errors import UsageError, UsageWarning
from jiracli.utils import get_text_from_editor, print_output, Config, colorfunc, print_error, \
    WARNING

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


@six.add_metaclass(ABCMeta)
class Command(object):
    def __init__(self, jira, args):
        self.args = args
        self.jira = jira

    @abstractmethod
    def eval(self):
        raise NotImplementedError

    def execute(self):
        return self.eval()

    def extract_extras(self):
        try:
            extras = {}
            for item in self.args.extra_fields:
                key, value = item.split("=")
                try:
                    value = json.loads(value)
                except ValueError:
                    pass
                if key in extras:
                    if not isinstance(extras[key], list):
                        v = [extras[key]]
                        extras[key] = v
                    extras[key].append(value)
                else:
                    extras[key] = value
            return extras
        except Exception:
            raise UsageWarning("Unknown extra fields %s" % (self.args.extra_fields))


class AdjustParentEstimateCommand(Command):
    def eval(self):
        if self.args.search_freetext:
            issues = self.jira.search_issues(self.args.search_freetext, project=self.args.project)
        elif self.args.search_jql:
            issues = self.jira.search_issues_jql(self.args.search_jql)
        elif self.args.filter:
            issues = self.jira.get_issues_by_filter(*self.args.filter)
        else:
            issues = [issue for issue in [self.jira.get_issue(jira) for jira in self.args.jira_ids] if issue is not None]

        for issue in issues:
            # get the time estimate values

            if "student" in issue["labels"]:
                print_output(u"{} is a student task, skipping...\n".format(issue["key"]))
                continue

            estimate = self.spent_time_or_estimate(issue, quiet=True)
            if estimate is None:
                print_error(u"{} has no time estimate\n".format(issue["key"]), severity=WARNING)
                continue

            # get the epic of this issue (warning if none)
            bookkeeping_story = self.get_parent_story(issue)
            if bookkeeping_story is None:
                print_error(u"{} has no parent story. Assignee: {}\n".format(issue["key"],
                                                                             issue["assignee"]),
                            severity=WARNING)
                continue

            # check if the issue in question was already mentioned in the comments
            if self.issue_already_substracted(issue, bookkeeping_story):
                print_output(u"{} already mentioned in the comments of {}\n".format(issue["key"],
                                                                                    bookkeeping_story[
                                                                                        "key"]))
            else:
                self.adjust_story_timetracking(bookkeeping_story, issue, dry=self.args.dry,
                                               verbose=(self.args.verbosity > 0))

    def get_parent_story(self, issue):
        """:returns: issue of type story linked as 'has parent' to the given issue"""
        try:
            links = issue["issuelinks"]
            parents = [link for link in links if link.type.name == "Refinement" \
                          and link.type.outward == "has parent" \
                          and link.outwardIssue.fields.issuetype.name == "Story"]
            return self.jira.get_issue(parents[0].outwardIssue.key)
        except:
            return None

    def spent_time_or_estimate(self, issue, quiet=False):
        """This function will return the time spent on an issue, when the time is less or equal
        to the original estimate, otherwise the original estimate is returned.

        We now want to run this function after the sprint has ended, thus an issue without a
        timelog will issue a warning.

        returns  [orininal, remaning]"""
        if "aggregatetimespent" not in issue or issue["aggregatetimespent"] == 0:
            if not quiet:
                print_error(u"No time was logged on {}\n".format(issue["key"]))
            return None

        if "timeoriginalestimate" not in issue or issue["timeoriginalestimate"] == 0:
            if not quiet:
                print_error(u"Missing time estimate for {}\n".format(issue["key"]))
            return None

        estimate = issue["timeoriginalestimate"]
        logged = issue["aggregatetimespent"]

        if not quiet and logged > estimate:
            print_error(u"Attention: {} was overbooked by {}\n".format(
                issue["key"], self.secs_to_human_readable(logged - estimate)), severity=WARNING)

        return min(estimate, logged)

    def get_epic(self, issue):
        """Get the epic of the issue"""
        try:
            return self.jira.get_issue(issue["customfield_10609"])
        except:
            return None

    def get_story_clone(self, epic):
        """Get the epic of the issue"""
        try:
            links = epic["issuelinks"]
            clones = [link for link in links if link.type.name == "Cloners"]
            return self.jira.get_issue(clones[0].inwardIssue.key)
        except:
            return None

    def issue_already_substracted(self, issue, story):
        return bool([comment for comment in [_.body for _ in story["comment"].comments] if issue["key"] in comment])

    def adjust_story_timetracking(self, story, issue, dry=True, verbose=True):
        timetracking = story["timetracking"]
        estimate = self.spent_time_or_estimate(issue)
        estimate_human_readable = self.secs_to_human_readable(estimate)
        issue = self.jira.get_issue(issue["key"], raw=True)
        message = str(u"{}: {}: reduced by {}".format(issue.fields.assignee.displayName, issue.key,
                                                      estimate_human_readable))

        new_original_raw = timetracking.originalEstimateSeconds - estimate
        new_remaining_raw = timetracking.remainingEstimateSeconds - estimate

        if new_original_raw < 0 or new_remaining_raw < 0:
            print_error(
                u"Story {} full. Estimate would become negative, skipping\n".format(story["key"]),
                severity=WARNING)
            return

        new_original = self.secs_to_human_readable(new_original_raw)
        new_remaining = self.secs_to_human_readable(new_remaining_raw)

        if verbose:
            msg = u"Adjusting estimate of story [{}]: {}".format(story["key"], story["summary"])
            msg += u"\nby issue [{}]: {}".format(issue.key, issue.fields.summary)
            print_output(colorfunc(msg, "blue"))
            print_output(u"{}: {} - {} = {}".format(colorfunc("Original Estimate", "white"),
                                                    timetracking.originalEstimate,
                                                    estimate_human_readable,
                                                    new_original))
            print_output(u"{}: {} - {} = {}".format(colorfunc("Remaning Estimate", "white"),
                                                    timetracking.remainingEstimate,
                                                    estimate_human_readable,
                                                    new_remaining))
            print_output("comment: {}".format(colorfunc(message, "white")))
            print("")

        if not dry:
            # fields = {
            #    "timetracking": {"originalEstimate": "3w 2d 1h", "remainingEstimate": "3w 2d 1h"}}
            story = self.jira.get_issue(story["key"], raw=True)
            story.update(fields={"timetracking": {
                "originalEstimate": new_original,
                "remainingEstimate": new_remaining
            }})
            self.jira.add_comment(story, message)

    def secs_to_human_readable(self, estimate):
        estimate_human_readable = ""
        wdhm = OrderedDict()
        wdhm["w"] = 60 * 60 * 8 * 5
        wdhm["d"] = 60 * 60 * 8
        wdhm["h"] = 60 * 60
        wdhm["m"] = 60
        for unit, quot in wdhm.items():
            if old_div(estimate, quot) != 0:
                estimate_human_readable += " {}{}".format(old_div(estimate, quot), unit)
                estimate = estimate % quot
        if estimate:
            estimate_human_readable += " {}{}".format(estimate, "s")
        return estimate_human_readable.strip()


class WorkLogCommand(Command):
    def eval(self):
        # TODO: evaluate the user and show worklog only for the selected user
        if self.args.spent:
            self.log_work()
        self.show_work_log()

    def log_work(self):
        if self.args.comment:
            comment = self.args.comment[0]
        else:
            comment = ""
        if self.args.remaining:
            remaining = self.args.remaining[0]
        else:
            remaining = None
        self.jira.log_work(issue=self.args.jira_id, spent=self.args.spent[0],
                           comment=comment, remaining=remaining)

    def show_work_log(self):
        issue = self.jira.get_issue(self.args.jira_id)
        if not issue:
            return

        if "timetracking" in issue and hasattr(issue["timetracking"], "originalEstimate"):
            print_output("{}: {}".format(
                colorfunc("Estimated", "white"),
                colorfunc(issue["timetracking"].originalEstimate, "blue")))

            print_output("{}: {}".format(
                colorfunc("Remaining", "white"),
                colorfunc(issue["timetracking"].remainingEstimate, "blue")))

            time_spent_seconds = getattr(issue["timetracking"], "timeSpentSeconds", 0)

            if time_spent_seconds <= issue["timetracking"].originalEstimateSeconds:
                color = "green"
            else:
                color = "red"

            print_output("{}: {}".format(
                colorfunc("Logged   ", "white"),
                colorfunc(
                    getattr(issue["timetracking"], "timeSpent", str(time_spent_seconds) + "m"),
                    color)))
        print_output("")

        worklogs = issue["worklog"].worklogs
        for worklog in worklogs:
            print_output(self.format_worklog(worklog))

    def format_worklog(self, worklog):
        return "%s %s : %s %s" % (
            colorfunc(worklog.created, "blue"),
            colorfunc(worklog.author, "white"),
            worklog.comment, colorfunc("[" + worklog.timeSpent + "]", "green"))


class ViewCommand(Command):
    def eval(self):
        if self.args.oneline:
            mode = -1
        elif self.args.verbosity > 1:
            mode = self.args.verbosity
        else:
            mode = 0
        if self.args.search_freetext:
            issues = self.jira.search_issues(self.args.search_freetext, project=self.args.project)
        elif self.args.search_jql:
            issues = self.jira.search_issues_jql(self.args.search_jql)
        elif self.args.filter:
            issues = self.jira.get_issues_by_filter(*self.args.filter)
        else:
            issues = [issue for issue in [self.jira.get_issue(jira) for jira in self.args.jira_ids] if issue is not None]

        for issue in issues:
            print_output(self.jira.format_issue(
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
            'versions': (self.jira.list_versions, 'project'),
            'transitions': (self.jira.get_available_transitions, 'issue'),
            'filters': (self.jira.get_filters,),
            'aliases': (lambda: [{"name": k, "description": v} for k, v in
                                 list(Config(section='alias').items()).items()],)
        }
        func, arguments = mappers[self.args.type][0], mappers[self.args.type][1:]
        _ = []
        _k = {}
        for earg in arguments:
            if isinstance(earg, tuple):
                if getattr(self.args, earg[0]):
                    _k.update({earg[0]: getattr(self.args, earg[0])})
                else:
                    _k[earg[0]] = earg[1]
            else:
                if not getattr(self.args, earg):
                    raise UsageError("'--%s' is required for listing '%s'" % (earg, self.args.type))
                _.append(getattr(self.args, earg))
        found = False
        data = func(*_, **_k)
        data_dict = OrderedDict()
        if type(data) == type([]):
            for item in data:
                data_dict[item['name']] = item
        else:
            data_dict = data
        for item in list(data_dict.values()):
            found = True
            val = item
            if type(item) == type({}):
                val = colorfunc(item['name'], 'white')
                if 'key' in item and item['key']:
                    val += " [" + colorfunc(item['key'], 'magenta') + "]"
                if 'description' in item and item['description']:
                    val += " [" + colorfunc(item['description'], 'green') + "]"
            print_output(colorfunc(val, 'white'))
        if not found:
            raise UsageWarning("No %s found." % self.args.type)


class UpdateCommand(Command):
    def eval(self):
        if self.args.extra_fields:
            extras = self.extract_extras()
            self.jira.update_issue(
                self.args.issue,
                **extras
            )
        if self.args.issue_comment:
            self.jira.add_comment(
                self.args.issue, self.args.issue_comment if isinstance(self.args.issue_comment,
                                                                       basestring) else get_text_from_editor()
            )
            print_output(
                self.jira.format_issue(self.jira.get_issue(self.args.issue), comments_only=True))
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
            current_components = set(
                k["name"] for k in self.jira.get_issue(self.args.issue)["components"])
            if not set(self.args.issue_components).issubset(current_components):
                new_components = current_components.union(self.args.issue_components)
                self.jira.update_issue(self.args.issue,
                                       components=[components[k] for k in new_components]
                                       )
                print_output(colorfunc(
                    'component(s): %s added to %s' % (
                        ",".join(self.args.issue_components), self.args.issue), 'green'
                ))
            else:
                raise UsageWarning("component(s):[%s] already exist in %s" % (
                    ",".join(self.args.issue_components), self.args.issue)
                                   )
        elif self.args.issue_transition:
            self.jira.transition_issue(
                self.args.issue, self.args.issue_transition.lower(),
                self.args.resolution
            )
            print_output(colorfunc(
                '%s transitioned to "%s"' % (self.args.issue, self.args.issue_transition), 'green'
            ))
        elif self.args.issue_assignee:
            self.jira.assign_issue(self.args.issue, self.args.issue_assignee)
            print_output(colorfunc(
                '%s assigned to %s' % (self.args.issue, self.args.issue_assignee), 'green'
            ))
        elif self.args.labels:
            self.jira.add_labels(self.args.issue, self.args.labels, True)
            print_output(colorfunc(
                '%s labelled with %s' % (self.args.issue, ",".join(self.args.labels)), 'green'
            ))
        if self.args.affects_version:
            self.jira.add_versions(self.args.issue, self.args.affects_version, 'affects')
            print_output(colorfunc(
                'Added affected version(s) %s to %s' % (
                    ",".join(self.args.affects_version), self.args.issue), 'green'
            ))
        if self.args.remove_affects_version:
            self.jira.remove_versions(self.args.issue, self.args.remove_affects_version, 'affects')
            print_output(colorfunc(
                'Removed affected version(s) %s from %s' % (
                    ",".join(self.args.remove_affects_version), self.args.issue), 'blue'
            ))
        if self.args.fix_version:
            self.jira.add_versions(self.args.issue, self.args.fix_version, 'fix')
            print_output(colorfunc(
                'Added fixed version(s) %s to %s' % (
                    ",".join(self.args.fix_version), self.args.issue), 'green'
            ))
        if self.args.remove_fix_version:
            self.jira.remove_versions(self.args.issue, self.args.remove_fix_version, 'fix')
            print_output(colorfunc(
                'Removed fixed version(s) %s from %s' % (
                    ",".join(self.args.remove_fix_version), self.args.issue), 'blue'
            ))


class AddCommand(Command):
    def eval(self):
        extras = {}
        if self.args.extra_fields:
            extras = self.extract_extras()
        if not self.args.issue_project:
            raise UsageError('project must be specified when creating an issue')
        if not (self.args.issue_parent or self.args.issue_type):
            self.args.issue_type = 'bug'
        if self.args.issue_type and not self.args.issue_type.lower() in list(self.jira.get_issue_types().keys()) + list(self.jira.get_subtask_issue_types().keys()):
            raise UsageError(
                "invalid issue type: %s (try using jira-cli "
                "list issue_types or jira-cli list subtask_types)" % self.args.issue_type
            )
        if self.args.issue_parent:
            if not self.args.issue_type:
                self.args.issue_type = 'sub-task'
            if self.args.issue_type not in self.jira.get_subtask_issue_types():
                raise UsageError(
                    "issues created with parents must be one of {%s}" % ",".join(
                        self.jira.get_subtask_issue_types())
                )
        components = {}
        if self.args.issue_components:
            valid_components = dict(
                (k["name"], k["id"]) for k in self.jira.get_components(
                    self.args.issue_project
                )
            )
            if not set(self.args.issue_components).issubset(valid_components):
                raise UsageError(
                    "components for project %s should be one of {%s}" % (
                        self.args.issue_project, ",".join(valid_components)
                    )
                )
            else:
                components = {k: valid_components[k] for k in self.args.issue_components}
        if self.args.issue_description is not None:
            description = self.args.issue_description
        else:
            description = get_text_from_editor()
        print_output(self.jira.format_issue(
            self.jira.create_issue(
                self.args.issue_project, self.args.issue_type, self.args.title, description,
                self.args.issue_priority, self.args.issue_parent, self.args.issue_assignee,
                self.args.issue_reporter, self.args.labels, components, **extras
            )
        ))
