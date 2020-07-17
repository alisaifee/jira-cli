#!/usr/bin/env python3
"""

"""
from __future__ import print_function
from builtins import str
import argparse
import keyring
import shlex
import sys
from suds import WebFault

from jiracli import __version__
from jiracli.bridge import get_bridge
from jiracli.cache import clear_cache
from jiracli.errors import JIRAError
from jiracli.errors import JiraAuthenticationError, JiraInitializationError
from jiracli.errors import UsageWarning, JiraCliError, UsageError
from jiracli.processor import ListCommand
from jiracli.processor import ViewCommand, AddCommand, UpdateCommand, WorkLogCommand, \
    AdjustParentEstimateCommand
from jiracli.utils import print_error, WARNING, Config, colorfunc, prompt, \
    print_output


def initialize(config, base_url=None, username=None, password=None,
               persist=True, error=False, protocol='rest'):
    url = base_url or config.base_url
    bridge = get_bridge(protocol)(url, config, persist) if (url and not error) else None
    if error or not (url and bridge and bridge.ping()):
        url = url or prompt("Base url for the jira instance: ")
        username = (
                username or
                (not error and config.username) or
                prompt("username: ")
        )
        password = (
                password or
                (not error and keyring.get_password('jira-cli', username)) or
                prompt("password: ", True)
        )
        jira = not error and bridge or get_bridge(protocol)(url, config, persist)
        persist_warning = "would you like to persist the credentials to the local keyring? [y/n]:"

        first_run = (
            not (
                    config.base_url or
                    config.username or
                    keyring.get_password('jira-cli', username)
            )
        )
        if persist or first_run:
            config.base_url = url
            config.save()
            keyring.set_password('jira-cli', username, password)
        try:
            jira.login(username, password)
            if (
                    (persist or first_run) and
                    (not (config.username == username or config.password == password)) and
                    "y" == prompt(persist_warning)
            ):
                config.username = username
                keyring.set_password('jira-cli', username, password)
                config.save()
            config.save()
            return jira
        except JiraAuthenticationError:
            print_error("invalid username/password", severity=WARNING)
            return initialize(config, base_url=url, error=True, protocol=protocol, persist=persist)
        except JiraInitializationError:
            print_error("invalid jira location", severity=WARNING)
            config.base_url = ""
            return initialize(config, error=True, protocol=protocol, persist=persist)
    else:
        return bridge


def build_parser():
    parser = argparse.ArgumentParser(description='jira-cli')
    parser.add_argument("--version", action="store_true",
                        help="print the version of jira-cli")
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='jira sub commands')
    base = argparse.ArgumentParser(description='jira-cli-base', add_help=False)
    base.add_argument('--jira-url', dest='jira_url',
                      help='the base url for the jira instance', default=None)
    base.add_argument("--format", dest="format", default=None,
                      help=r'format for displaying ticket information. '
                           r'allowed tokens: status,priority,updated,votes,'
                           r'components,project,reporter,created,fixVersions,'
                           r'summary,environment,assignee,key,'
                           r'affectsVersions,type.'
                           r'Use the %% character before each token '
                           r'(example: issue id: %%key [%%priority])')
    base.add_argument('--oneline', dest='oneline',
                      help='built in format to display each ticket on one line',
                      action='store_true')
    base.add_argument('-v', dest='verbosity', help='amount of detail to show for issues',
                      action='count', default=0)
    base.add_argument('-u', '--username', dest='username',
                      help='username to login as', default=None)
    base.add_argument('-p', '--password', dest='password',
                      help='password for jira instance', default=None)

    view = subparsers.add_parser('view', parents=[base], help='view/list/search for issues')
    view.set_defaults(cmd=ViewCommand)
    work_log = subparsers.add_parser("work-log", parents=[base], help="show work log/log work")
    work_log.set_defaults(cmd=WorkLogCommand)
    add = subparsers.add_parser('new', parents=[base], help='create a new issue')
    add.add_argument('--extra', dest='extra_fields',
                     nargs='?', action='append',
                     help='extra fields for the new ticket')
    add.set_defaults(cmd=AddCommand)
    update = subparsers.add_parser('update', parents=[base], help='update existing issues')
    update.set_defaults(cmd=UpdateCommand)
    list = subparsers.add_parser('list', parents=[base], help='list jira types and properties')
    list.set_defaults(cmd=ListCommand)

    trefix = subparsers.add_parser("trefix", parents=[base],
                                   help="adjust time estimate of corresponding parent story according to TRE-R rules")
    trefix.set_defaults(cmd=AdjustParentEstimateCommand)
    # TODO: do this by inheriting this group of arguments (so share between adjust and view)
    search_args = trefix.add_mutually_exclusive_group(required=False)
    search_args.add_argument('--search', dest='search_freetext')
    search_args.add_argument('--search-jql', dest='search_jql',
                             help='search using JQL')
    search_args.add_argument('--filter', dest='filter', help='filter(s) to use',
                             action='append')
    trefix.add_argument('jira_ids', nargs='*', help='jira issue ids')
    trefix.add_argument("--dry", dest="dry",
                        help="Do not actually perform the action but show what would happen",
                        action="store_true")

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
    view.add_argument('jira_ids', nargs='*', help='jira issue ids')

    work_log.add_argument("jira_id", help="jira issue id")
    work_log.add_argument("--comment", dest="comment", help="work log description", nargs=1)
    work_log.add_argument("--spent", dest="spent", help="the time spent working", nargs=1)
    work_log.add_argument("--remaining", dest="remaining",
                          help="set remaining estimate to new value", nargs=1)

    list.add_argument('type', choices=['filters', 'projects', 'issue_types',
                                       'subtask_types', 'priorities',
                                       'statuses', 'components', 'versions', 'resolutions',
                                       'transitions', 'aliases'])
    list.add_argument('--project', help='the jira project to use when listing components',
                      dest='project')
    list.add_argument('--issue', help='the jira issue to use when listing transitions',
                      dest='issue')
    list.add_argument('--group', help='the jira user group to use when listing users',
                      dest='group')

    add.add_argument('title', help='new issue title')
    add.add_argument('--priority', dest='issue_priority',
                     help='new issue priority', default='minor')
    add.add_argument('--project', dest='issue_project',
                     help='project to create new issue in')
    add.add_argument('--description', dest='issue_description',
                     help='description of new issue', default=None)
    add.add_argument('--type', dest='issue_type', help='new issue priority')
    add.add_argument('--parent', dest='issue_parent',
                     help='parent of new issue')
    add.add_argument('--label', dest='labels',
                     nargs='?', action='append',
                     help='label to add to the ticket')
    add.add_argument('--assignee', dest='issue_assignee', help='new issue assignee')
    add.add_argument('--reporter', dest='issue_reporter', help='new issue reporter')
    add.add_argument('--component', dest='issue_components',
                     action='append', help='components(s) for the new issue'
                                           ' (use list components to view available components)')

    update.add_argument('issue', help='the jira issue to act on')

    # ridiculous hack to allow for passing in --comment or --comment="....".
    # when no string is passed in the text editor will be launched to enter the comment
    class CommentAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string):
            setattr(namespace, self.dest, values or True)

    update.add_argument(
        '--comment', dest='issue_comment', nargs='?', help='add a comment to an existing issue',
        action=CommentAction
    )
    update.add_argument('--priority', '--priority', dest='issue_priority',
                        help='change the priority of an issue')
    update.add_argument('--component', dest='issue_components',
                        action='append', help='add components(s) to an issue'
                                              ' (use list components to view available components)')
    update.add_argument('--assign', dest='issue_assignee',
                        help='assign the issue to a user')
    update.add_argument('--transition', dest='issue_transition',
                        help='transition the issue to a new state'
                             ' (use list transitions to view available transitions for an issue)')
    update.add_argument('--label', dest='labels',
                        nargs='?', action='append',
                        help='label to add to the ticket')
    update.add_argument('--resolution', dest='resolution',
                        help='set the resolution for the issue')
    update.add_argument('--fix-version', dest='fix_version',
                        nargs='?', action='append',
                        help='add a version that this issue fixes')
    update.add_argument('--remove-fix-version', dest='remove_fix_version',
                        nargs='?', action='append',
                        help='remove a version specified as being fixed by the issue')
    update.add_argument('--affects-version', dest='affects_version',
                        nargs='?', action='append',
                        help='add a version that this issue affects')
    update.add_argument('--remove-affects-version', dest='remove_affects_version',
                        nargs='?', action='append',
                        help='remove a version specified as being affected by the issue')
    update.add_argument('--extra', dest='extra_fields',
                        nargs='?', action='append',
                        help='extra fields to update in the ticket')

    subparsers.add_parser("configure", help='configure jira-cli interactively')
    subparsers.add_parser("clear_cache", help='clear the jira-cli cache')

    return parser


def cli(args=sys.argv[1:]):
    import optparse
    alias_config = Config(section='alias')
    if set(list(alias_config.items().keys())).intersection(args):
        for alias, target in list(alias_config.items()).items():
            if args[0] == alias:
                args = shlex.split(target) + args[1:]
                break
    parser = build_parser()
    try:
        config = Config()
        pre_opts, pre_args = None, None
        try:
            optparser = optparse.OptionParser()

            def void(*args):
                raise SystemExit()

            optparser.print_usage = void
            optparser.add_option("", "--version", action='store_true', default=False)
            pre_opts, pre_args = optparser.parse_args(args)
        except SystemExit:
            pass
        if pre_opts and pre_opts.version:
            print(__version__)
            return
        if not (pre_opts and ("configure" in pre_args or "clear_cache" in pre_args)):
            post_args = parser.parse_args(args)
            jira = initialize(
                config, post_args.jira_url, post_args.username, post_args.password,
                persist=not (post_args.username or post_args.jira_url),
                protocol='rest'
            )
            return post_args.cmd(jira, post_args).execute()
        else:
            if "configure" in pre_args:
                config.reset()
                initialize(
                    config, "", "", "", True,
                    protocol='rest'
                )
            elif "clear_cache" in pre_args:
                clear_cache()
                print_output(colorfunc("jira-cli cache cleared", "green"))
            return

    except KeyboardInterrupt:
        print_error("aborted", severity=WARNING)
    except UsageWarning as e:
        print_error(str(e), severity=WARNING)
    except (JiraCliError, UsageError) as e:
        print_error(str(e))
    except (WebFault) as e:
        print_error(JiraCliError(e))
    except (JIRAError) as e:
        print_error(JiraCliError(e))
    except NotImplementedError as e:
        print_error(e)


if __name__ == "__main__":
    cli()
