"""

"""
import argparse

from suds import WebFault

from jiracli.bridges import get_bridge
from jiracli.errors import JiraAuthenticationError, JiraInitializationError
from jiracli.errors import  UsageWarning, JiraCliError, UsageError
from jiracli.processor import ViewCommand, AddCommand, UpdateCommand
from jiracli.processor import ListCommand
from jiracli.utils import print_error, WARNING, Config, colorfunc, prompt


def initialize(config, base_url=None, username=None, password=None,
               persist=True, error=False, protocol='soap'):
    url = base_url or config.base_url
    bridge = get_bridge(protocol)(url, config, persist) if (url and not error) else None
    if error or not (url and bridge and bridge.ping()):
        url = url or prompt("Base url for the jira instance: ")
        username = (
            username
            or (not error and config.username)
            or prompt("username: ")
        )
        password = (
            password
            or (not error and config.password)
            or prompt("password: ", True)
        )
        jira = get_bridge(protocol)(url, config, persist)
        persist_warning = "would you like to persist the credentials to ~/.jira_cli/config.cfg?\n{0} [y/n]:"
        persist_warning = persist_warning.format(colorfunc('[WARNING: this will '
                                                  'store credentials in plaintext', 'red'))
        first_run = (
            not(
                config.base_url
                or config.username
                or config.password
            )
        )
        if persist or first_run:
            config.base_url = url
            config.save()
        try:
            jira.login(username, password)
            if (
                (persist or first_run)
                 and (
                    not (
                        config.username == username
                        or config.password == password
                    )
                )
                and "y" == prompt(persist_warning)
            ):
                config.username = username
                config.password = password
                config.save()
            config.save()
            return jira
        except JiraAuthenticationError:
            print_error("invalid username/password", severity=WARNING)
            return initialize(config, base_url=url, error=True, protocol=protocol, persist=persist)
        except JiraInitializationError:
            print_error("invalid jira location", severity=WARNING)
            return initialize(config, error=True, protocol=protocol, persist=persist)
    else:
        return bridge


def build_parser():
    parser = argparse.ArgumentParser(description='jira-cli')

    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='additional help')
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
    base.add_argument('-v', dest='verbosity', help='amount of detail to show',
                        action='count')
    base.add_argument('-u', '--username', dest='username',
                        help='username to login as', default=None)
    base.add_argument('-p', '--password', dest='password',
                        help='password for jira instance', default=None)
    base.add_argument('--protocol', dest='protocol',
                        choices = ['soap','rest'], help='the protocol to use to communicate with jira',
                        default='soap')

    view = subparsers.add_parser('view', parents=[base])
    view.set_defaults(cmd=ViewCommand)
    add = subparsers.add_parser('new', parents=[base])
    add.set_defaults(cmd=AddCommand)
    update = subparsers.add_parser('update', parents=[base])
    update.set_defaults(cmd=UpdateCommand)
    list = subparsers.add_parser('list', parents=[base])
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
    view.add_argument('jira_ids', nargs='*')


    list.add_argument('type', choices=['filters', 'projects', 'issue_types',
                                       'subtask_types', 'priorities',
                                       'statuses', 'components', 'resolutions',
                                       'transitions'])
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
    update.add_argument('--assign', dest='issue_assignee',
                        help='assign the issue to a user')
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
            persist=not (args.username or args.jira_url),
            protocol=config.protocol or args.protocol
        )
        args.cmd(jira, args).eval()
    except KeyboardInterrupt:
        print_error("aborted", severity=WARNING)
    except UsageWarning, e:
        print_error(str(e), severity=WARNING)
    except (JiraCliError, UsageError), e:
        print_error(str(e))
    except (WebFault), e:
        print_error(JiraCliError(e))
    except NotImplementedError,e:
        print_error(e)
if __name__ == "__main__":
    cli()