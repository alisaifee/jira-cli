import tempfile
import unittest

import mock

import jiracli
from jiracli.errors import JiraAuthenticationError, JiraInitializationError
from jiracli.interface import build_parser, initialize
from jiracli.processor import ViewCommand
from jiracli.utils import Config
from jiracli.interface import cli


class CliParsingTests(unittest.TestCase):
    def setUp(self):
        self.stderr_patcher = mock.patch("sys.stderr")
        self.stderr = self.stderr_patcher.start()

    def test_base_url_provided(self):
        parser = build_parser()
        args = parser.parse_args("list projects --jira-url=http://foo.bar -u testuser -p testpass".split(" "))
        self.assertEqual(args.jira_url, 'http://foo.bar')
        self.assertEqual(args.username, 'testuser')
        self.assertEqual(args.password, 'testpass')

    def test_no_subcommand(self):
        parser = build_parser()
        self.assertRaises(SystemExit, parser.parse_args, "--jira-url=http://foo.bar -u testuser -p testpass".split(" "))

    def test_configure_argument(self):
        with mock.patch("jiracli.interface.print_output"):
            with mock.patch("jiracli.interface.prompt") as prompt:
                with mock.patch("jiracli.interface.initialize") as init:
                    cli(["--v1", "configure"])
                    cli(["configure"])
                    self.assertEqual(init.call_count, 2)

    def test_clear_cache_argument(self):
        with mock.patch("jiracli.interface.print_output"):
            with mock.patch("jiracli.interface.prompt") as prompt:
                with mock.patch("jiracli.interface.clear_cache") as clear_cache:
                    cli(["--v1" , "clear_cache"])
                    cli(["clear_cache"])
                    self.assertEqual(clear_cache.call_count, 2)

    def test_view_subcommand(self):
        parser = build_parser()
        args = parser.parse_args(
            "view TP-10".split(" ")
        )
        self.assertEqual(args.jira_ids, ['TP-10'])
        args = parser.parse_args(
            "view TP-10 TP-20".split(" ")
        )
        self.assertEqual(args.jira_ids, ['TP-10', 'TP-20'])
        args = parser.parse_args(
            ['view', '--search=test string']
        )
        self.assertEqual(args.cmd, ViewCommand)
        self.assertEqual(args.search_freetext, 'test string')
        args = parser.parse_args(
            ['view','--search-jql=test string']
        )
        self.assertEqual(args.search_jql, 'test string')
        self.assertRaises(SystemExit, parser.parse_args, 'view --search "blah" --search-jql="other blah"'.split(" "))

    def test_list_subcommand(self):
        parser = build_parser()
        for allowed in ['projects', 'statuses', 'resolutions', 'priorities']:
            self.assertEqual(
                parser.parse_args(['list', allowed]).type,
                allowed
            )


class CliInitParsing(unittest.TestCase):

    def setUp(self):
        self.stderr_patcher = mock.patch("sys.stderr")
        self.stderr = self.stderr_patcher.start()
        tmp_config = tempfile.mktemp()
        self.cfg = Config(tmp_config)

    def test_first_run(self):
        with mock.patch("jiracli.interface.prompt") as prompt:
            with mock.patch("jiracli.bridge.JiraSoapBridge") as bridge:
                def prompt_response(msg, *a):
                    if msg.startswith('username'):
                        return 'testuser'
                    if msg.startswith('password'):
                        return 'testpass'
                    if msg.startswith('Base'):
                        return 'http://www.foobar.com'
                bridge.return_value.ping.return_value = False
                prompt.side_effect = prompt_response
                bridge.return_value.ping.assert_call_count(1)
                bridge.return_value.login.assert_call_count(1)
                self.assertEqual(bridge.return_value, initialize(self.cfg))

    def test_first_run_with_error_and_persist(self):
        with mock.patch("jiracli.interface.prompt") as prompt:
            with mock.patch("jiracli.bridge.JiraSoapBridge") as bridge:
                def prompt_response(msg, *a):
                    if msg.startswith('username'):
                        return 'testuser'
                    if msg.startswith('password'):
                        return 'testpass'
                    if msg.startswith('Base'):
                        return 'http://www.foobar.com'
                    if msg.startswith('would you like'):
                        return 'y'
                self.c = 0
                def login(*a,**k):
                    try:
                        if self.c == 0:
                            raise JiraAuthenticationError()
                        if self.c == 1:
                            raise JiraInitializationError()
                        else:
                            return
                    finally:
                        self.c+=1
                prompt.side_effect = prompt_response
                bridge.return_value.login.side_effect = login
                bridge.return_value.ping.return_value = False
                bridge.return_value.ping.assert_call_count(1)
                bridge.return_value.login.assert_call_count(3)
                self.assertEqual(bridge.return_value, initialize(self.cfg, persist=True))

    def test_subsequent_run_with_persist(self):
        self.cfg.username = 'testuser'
        self.cfg.password = 'testpass'
        self.cfg.base_url = 'http://www.foobar.com'
        with mock.patch("jiracli.interface.prompt") as prompt:
            with mock.patch("jiracli.bridge.JiraSoapBridge") as bridge:
                prompt.assert_call_count(0)
                bridge.assert_call_args('testuser', 'testpass')
                bridge.return_value.login.assert_call_args('testuser', 'testpass')
                bridge.return_value.ping.return_value = False
                bridge.return_value.ping.assert_call_count(1)
                bridge.return_value.login.assert_call_count(3)
                self.assertEqual(bridge.return_value, initialize(self.cfg))

    def test_soap_token(self):
        with mock.patch("jiracli.bridge.JiraSoapBridge") as bridge:
            self.cfg.base_url = 'http://www.foobar.com'
            bridge.return_value.ping.return_value = True
            bridge.return_value.ping.assert_call_count(1)
            self.assertEqual(bridge.return_value, initialize(self.cfg))


class BackwardCompatibilityTests(unittest.TestCase):
    def setUp(self):
        tmp_config = tempfile.mktemp()
        self.cfg = Config(tmp_config)
        jiracli.utils.CONFIG_FILE = tmp_config

    def test_jira_cli_v1_invoked(self):
        with mock.patch("jiracli.interface.old_main") as old_main:
            self.cfg.v1 = "1"
            self.cfg.save()
            cli(['--help'])
            self.assertTrue(old_main.call_count==1)
            self.cfg.v1 = "True"
            self.cfg.save()
            cli(['--help'])
            self.assertTrue(old_main.call_count==2)

    def test_jira_cli_v2_invoked(self):
        with mock.patch("sys.stdout") as stdout:
            with mock.patch("jiracli.interface.old_main") as old_main:
                with mock.patch("jiracli.processor.Command.execute") as execute:
                    self.assertRaises(SystemExit, cli, ['--help', '--v2'])
                    self.assertRaises(SystemExit, cli, ['--help'])
                    self.assertRaises(SystemExit, cli, ['--help'])

