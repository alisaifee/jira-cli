import unittest

import mock

from jiracli.interface import build_parser, cli

class AddCommandTests(unittest.TestCase):
    def test_issue_type_parsing(self):
        "Previously, calling this would raise an exception on python3"
        with mock.patch("jiracli.interface.print_output"):
            with mock.patch("jiracli.interface.prompt") as prompt:
                with mock.patch("jiracli.interface.initialize") as init:
                    init().get_issue_types.return_value = {'story': 1}
                    cli("new title --type story --project FOO --description bar".split(" "))

