"""
utility functions
"""

import getpass
import os
import tempfile
import sys
from six.moves import configparser, input
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
    def __init__(self, path=None):
        """
        manages a the .cfg file
        """
        object.__setattr__(self, 'cfg', configparser.ConfigParser())
        object.__setattr__(self, 'section', 'jira')
        object.__setattr__(self, 'cfg_path', path or CONFIG_FILE)
        if os.path.isfile(self.cfg_path):
            self.cfg.read(self.cfg_path)

    def save(self):
        if not os.path.isdir(os.path.split(self.cfg_path)[0]):
            os.makedirs(os.path.split(self.cfg_path)[0])
        self.cfg.write(open(self.cfg_path, 'w'))

    def reset(self):
        for section in self.cfg.sections():
            self.cfg.remove_section(section)
        self.save()

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
            try:
                return cfg.getboolean(section, item)
            except (Exception):
                try:
                    return cfg.getint(section, item)
                except (Exception):
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
    for k, v in asdict(d).items():
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
    for k, v in d.items():
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
    sys.stderr.write(colorfunc(msg, color) + "\n")

def print_output(msg):
    print(msg.encode('utf-8'))

def prompt(msg, masked=False):
    return input(msg) if not masked else getpass.getpass(msg)
