"""
utility functions
"""

import ConfigParser
import getpass
import os
import tempfile
import sys
from jira import resources

from suds.sudsobject import asdict

import logging
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

CONFIG_DIR = os.path.expanduser('~/.jira-cli')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.cfg')
COLOR = True
DEFAULT_EDITOR_TEXT = """-- enter your text here
-- all lines starting with '--' will be removed"""


class Config(object):
    __slots__ = ['cfg', 'section']
    def __init__(self, path=None):
        """
        manages a the .cfg file
        """
        object.__setattr__(self, 'cfg', ConfigParser.ConfigParser())
        object.__setattr__(self, 'section', 'jira')
        if path:
            self.cfg.read(path)
        else:
            if os.path.isfile(CONFIG_FILE):
                self.cfg.read(CONFIG_FILE)

    def save(self):
        self.cfg.write(open(CONFIG_FILE, 'w'))

    def __setattr__(self, key, value):
        try:
            object.__getattribute__(self, key)
            object.__setattr__(self, key, value)
        except AttributeError:
            if not self.cfg.has_section(self.section):
                self.cfg.add_section(self.section)
            self.cfg.set(self.section, key, value)


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

def rest_recursive_dict(d):
    """
    recursively serializes a jira-rest dictionary in to
    a pure python dictionary.
    """
    out = {}
    import bpython
    bpython.embed(locals_ = locals())
    for k, v in d.iteritems():
        if v.__class__.__name__ == 'PropertyHolder':
            out[k] = v.__dict__
        else:
            out[k] = v
    return out


def map_rest_resource(resource):
    """
    convert jira.resource types to their id/key
    mappings as expected by the formatter/cli
    code.
    """
    resource_mapping = {
        resources.User: 'name',
        resources.IssueType: 'id',
        resources.Status: 'id',
        resources.Priority: 'id',
        resources.Component: 'id',
    }
    if type(resource) in resource_mapping:
        return getattr(resource, resource_mapping[type(resource)])
    return resource


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
        return "\n".join(
            [k for k in open(tmp).read().split("\n") if not k.startswith("--")])
    finally:
        if tmp and os.path.isfile(tmp):
            os.unlink(tmp)


CRITICAL = 0
WARNING = 1


def print_error(msg, severity=CRITICAL):
    color = 'red' if severity == CRITICAL else 'yellow'
    print >> sys.stderr, colorfunc(msg, color)

def print_output(msg):
    print(msg)

def prompt(msg, masked=False):
    return raw_input(msg) if not masked else getpass.getpass(msg)
