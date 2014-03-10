"""
utility functions
"""

import ConfigParser
import os
import tempfile
import sys

from suds.sudsobject import asdict


CONFIG_DIR = os.path.expanduser('~/.jira-cli')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.cfg')
COLOR = True
DEFAULT_EDITOR_TEXT = """-- enter your text here
-- all lines starting with '--' will be removed"""


class Config(object):
    def __init__(self):
        """
        manages a the .cfg file
        """
        self.cfg = ConfigParser.ConfigParser()
        self.section = 'jira'
        if os.path.isfile(CONFIG_FILE):
            self.cfg.read(CONFIG_FILE)

    def save(self):
        self.cfg.write(open(CONFIG_FILE, 'w'))

    def add_option(self, key, value):
        if not self.cfg.has_section(self.section):
            self.cfg.add_section(self.section)
        self.cfg.set(self.section, key, value)
        return value

    def __getattribute__(self, item):
        cfg = super(Config, self).__getattribute__('cfg')
        section = super(Config, self).__getattribute__('section')
        if cfg.has_option(section, item):
            return cfg.get(section, item)
        else:
            try:
                return super(Config, self).__getattribute__(item)
            except AttributeError:
                return None


def soap_recursive_dict(d):
    """
    recursively serializes a soap dictionary in to
    a pure python dictionary.
    """
    out = {}
    for k, v in asdict(d).iteritems():
        if hasattr(v, '__keylist__'):
            out[k] = soap_recursive_dict(v)
        elif isinstance(v, list):
            out[k] = []
            for item in v:
                if hasattr(item, '__keylist__'):
                    out[k].append(soap_recursive_dict(item))
                else:
                    out[k].append(item)
        else:
            out[k] = v
    return out

from termcolor import colored as colorfunc
if not sys.stdout.isatty():
    colorfunc = lambda *a, **k: str(a[0])
    COLOR = False


def get_text_from_editor(def_text=DEFAULT_EDITOR_TEXT):
    """
    prompts for text using the default
    text editor on the system.
    """
    tmp = ""
    try:
        tmp = tempfile.mktemp()
        open(tmp, "w").write(def_text)
        editor = os.environ.setdefault("EDITOR", "vim")
        os.system("%s %s" % (editor, tmp))
        return "\n".join([k for k in open(tmp).read().split("\n") if not k.startswith("--")])
    finally:
        if tmp and os.path.isfile(tmp):
            os.unlink(tmp)



CRITICAL = 0
WARNING = 1


def print_error(msg, severity=CRITICAL):
    color = 'red' if severity == CRITICAL else 'yellow'
    print >> sys.stderr, colorfunc(msg, color)


