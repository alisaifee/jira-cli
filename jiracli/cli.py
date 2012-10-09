import getpass
import re
import os
import optparse
import tempfile
import xmlrpclib
import collections
import socket
import pickle
import sys
import xml
from termcolor import colored as colorfunc

jiraobj = None
token = None
type_dict = {}
jirabase=None
color = True
if not sys.stdout.isatty():
    colorfunc = lambda *a,**k:str(a[0])
    color = False
default_editor_text = """-- enter the text for the %s
-- all lines starting with '--' will be removed"""


def get_text_from_editor(def_text):
    tmp = tempfile.mktemp()
    open(tmp, "w").write(def_text)
    editor = os.environ.setdefault("EDITOR","vim")
    os.system("%s %s" % (editor, tmp))
    return "\n".join([k for k in open(tmp).read().split("\n") if not k.startswith("--")])


def setup_home_dir():
    if not os.path.isdir(os.path.expanduser("~/.jira-cli")):
        os.makedirs(os.path.expanduser("~/.jira-cli"))

def get_issue_type(issuetype):
    if issuetype:
        issuetype = issuetype.lower()
    if os.path.isfile(os.path.expanduser("~/.jira-cli/types.pkl")):
        issue_types = pickle.load(open(os.path.expanduser("~/.jira-cli/types.pkl"),"rb"))
    else:
        issue_types = jiraobj.jira1.getIssueTypes(token)
        pickle.dump(issue_types,  open(os.path.expanduser("~/.jira-cli/types.pkl"),"wb"))

    if not issuetype:
        return issue_types
    else:
        for t in issue_types:
            if t["name"].lower() == issuetype:
                return t["id"]

def get_issue_status(stat):
    if stat:
        stat = stat.lower()
    if os.path.isfile(os.path.expanduser("~/.jira-cli/statuses.pkl")):
        issue_stats = pickle.load(open(os.path.expanduser("~/.jira-cli/statuses.pkl"),"rb"))
    else:
        issue_stats = jiraobj.jira1.getStatuses(token)
        pickle.dump(issue_stats,  open(os.path.expanduser("~/.jira-cli/statuses.pkl"),"wb"))

    if not stat:
        return issue_stats
    else:
        for t in issue_stats:
            if t["id"].lower() == stat:
                return t["name"]

def get_issue_priority(priority):
    if priority:
        priority=priority.lower()
    if os.path.isfile(os.path.expanduser("~/.jira-cli/priorities.pkl")):
        issue_priorities = pickle.load(open(os.path.expanduser("~/.jira-cli/priorities.pkl"),"rb"))
    else:
        issue_priorities = jiraobj.jira1.getPriorities(token)
        pickle.dump(issue_priorities,  open(os.path.expanduser("~/.jira-cli/priorities.pkl"),"wb"))

    if not priority:
        return issue_priorities
    else:
        for t in issue_priorities:
            if t["name"].lower() == priority:
                return t["id"]

def search_issues ( criteria ):
    return jiraobj.jira1.getIssuesFromTextSearch(token, criteria )

def check_auth(username, password):
    def _login(u,p):
        username,password = u,p
        if not u:
            username = raw_input("enter username:")
        if not p:
            password = getpass.getpass("enter password:")
        try:
            return jiraobj.jira1.login(username,  password)
        except:
            print(colorfunc("username or password incorrect, try again.", "red"))
            return _login(None,None)
    global jiraobj, token, jirabase

    setup_home_dir()
    def _validate_jira_url(url=None):
        global jiraobj, token, jirabase
        if not url:
            jirabase = raw_input("base url for your jira instance (e.g http://issues.apache.org/jira):")
        else:
            jirabase = url
        try:
            jiraobj = xmlrpclib.ServerProxy("%s/rpc/xmlrpc" % jirabase )
            # lame ping method
            jiraobj.getIssueTypes()
        except (xml.parsers.expat.ExpatError, xmlrpclib.ProtocolError,socket.gaierror, IOError),  e:
            print colorfunc("invalid url %s. Please provide the correct url for your jira installation" % jirabase, "red")
            return _validate_jira_url()
        except Exception, e:
            open(os.path.expanduser("~/.jira-cli/config"),"w").write(jirabase)
        return None


    if os.path.isfile(os.path.expanduser("~/.jira-cli/config")):
        jirabase = open(os.path.expanduser("~/.jira-cli/config")).read().strip()
    _validate_jira_url( jirabase )
    if os.path.isfile(os.path.expanduser("~/.jira-cli/auth")):
        token = open(os.path.expanduser("~/.jira-cli/auth")).read()
    try:
        jiraobj = xmlrpclib.ServerProxy("%s/rpc/xmlrpc" % jirabase )
        jiraobj.jira1.getIssueTypes(token)
    except Exception, e:
        token = _login(username,password)
        open(os.path.expanduser("~/.jira-cli/auth"),"w").write(token)

def format_issue( issue , mode = 0, formatter=None):
    fields = {}
    global colorfunc
    status_color="blue"
    status_string = get_issue_status ( issue.setdefault("status","1")).lower()
    if status_string in ["resolved","closed"]:
        status_color="green"
    elif status_string in ["open","unassigned","reopened"]:
        status_color="red"

    special_fields = {"status":get_issue_status,"priority":get_issue_priority,"type":get_issue_type}

    if formatter:
        groups = re.compile("(%([\w]+))").findall(formatter)
        ret_str = formatter
        for k, v in groups:
            if v.lower() in special_fields.keys():
                meth = special_fields[v.lower()]
                key=issue[v.lower()]
                mappings = meth(None)
                data = ""
                for item in mappings:
                    if item['id'] == key:
                        data = item['name']
                ret_str = ret_str.replace(k, data)
            else:
                ret_str = ret_str .replace(k, issue.setdefault(v.lower(),""))
        return ret_str

    if mode >= 0:
        # minimal
        fields["issue"] = issue["key"]
        fields["status"] = colorfunc( get_issue_status ( issue["status"] )
                                    , status_color )
        fields["reporter"] = issue["reporter"]
        fields["assignee"] = issue.setdefault("assignee","")
        fields["summary"] = issue["summary"]
        fields["link"] = colorfunc( "%s/browse/%s" % ( jirabase, issue["key"]), "white",attrs=["underline"])
    if mode >= 1:
        fields["description"] = issue.setdefault("description","")
        fields["priority"] = get_issue_priority( issue["priority"] )
        fields["type"] = get_issue_type( issue["type"] )

    if mode < 0:
        url_str = colorfunc("%s/browse/%s" % (jirabase, issue["key"]), "white", attrs=["underline"])
        ret_str = colorfunc(issue["key"],status_color) +" "+ issue.setdefault("summary","") + " " + url_str
        if not color:
            ret_str += " [%s] " % get_issue_status(issue["status"])
        return ret_str
    return "\n".join( " : ".join((k.ljust(20),v)) for k,v in fields.items() ) + "\n"


def get_jira( jira_id ):
    """
    """
    try:
        return jiraobj.jira1.getIssue( token, jira_id )
    except:
        return {"key": jira_id }

def get_filters( ):
    saved = jiraobj.jira1.getSavedFilters( token )
    favorites = jiraobj.jira1.getFavouriteFilters (token)

    all_filters = dict( (k["name"], k) for k in saved )
    [all_filters.setdefault(k["name"], k) for k in favorites if k["name"] not in all_filters]
    return all_filters.values()

def get_filter_id_from_name ( name ):
    filters = [k for k in get_filters() if k["name"].lower() == name.lower()]
    if filters:
        return filters[0]["id"]
    else:
        raise RuntimeError("invalid filter name %s" % name )
def get_issues_from_filter( filter_name ):
    fid = get_filter_id_from_name( filter_name )
    if fid:
        return jiraobj.jira1.getIssuesFromFilter ( token, fid )
    return []

def add_comment( jira_id, comment ):
    if comment == default_editor_text:
        comment = get_text_from_editor(default_editor_text % ("comment"))
    res = jiraobj.jira1.addComment( token, jira_id, comment )
    if res:
        return "%s added to %s" % (comment, jira_id)
    else:
        return "failed to add comment to %s" % jira_id

def create_issue ( project, type=0, summary="", description="" , priority="Major"):
    if description == default_editor_text:
        description = get_text_from_editor(default_editor_text % ("new issue"))

    issue =  {"project":project.upper(), "type": get_issue_type(type), "summary":summary, "description":description, "priority": get_issue_priority(priority)}
    return jiraobj.jira1.createIssue( token, issue )


def main():
    """
    """
    example_usage = """
------------------------------------------------------------------------------------------
view jira: jira-cli BE-193
view multiple jiras: jira-cli XYZ-123 ZZZ-123 ABC-123
add a comment: jira-cli -j BE-193 -c "i am sam"
create a new issue: jira-cli -n bug -p BE -t "i am sam" "and this is my long description
ending
here"
------------------------------------------------------------------------------------------
"""
    parser = optparse.OptionParser()
    parser.usage = example_usage
    parser.add_option("-c","--comment",dest="comment", help="comment on a jira", action="store_true")
    parser.add_option("-j","--jira-id", dest="jira_id",help="issue id")
    parser.add_option("","--filter", dest="filter",help="filter(s) to use for listing jiras. use a comma to separate multiple filters")
    parser.add_option("-n","--new", dest = "issue_type", help="create a new issue with given title")
    parser.add_option("","--priority", dest = "issue_priority", help="priority of new issue", default="minor")
    parser.add_option("-t","--title", dest = "issue_title", help="new issue title")
    parser.add_option("-p","--project",dest="jira_project", help="the jira project to act on")
    parser.add_option("","--oneline",dest="oneline", help="print only one line of info", action="store_true")
    parser.add_option("","--list-jira-types",dest="listtypes", help="print out the different jira 'types'", action="store_true")
    parser.add_option("","--list-filters",dest="listfilters", help="print out the different jira filters available", action="store_true")
    parser.add_option("-v",dest="verbose", action="store_true", help="print extra information")
    parser.add_option("-s","--search",dest="search", help="search criteria" )
    parser.add_option("-f","--format",dest="format", default=None, help="""format for outputting information.
    allowed tokens: %status,%priority,%updated,%votes,%components,%project,%reporter,%created,%fixVersions,%summary,%environment,%assignee,%key,%affectsVersions,%type.
    examples: "%priority,%reporter","(%key) %priority, reported by %reporter"
    """)
    parser.add_option("","--user",dest="username", help="username to login as" , default=None)
    parser.add_option("","--password",dest="password", help="passowrd", default = None )

    opts, args = parser.parse_args()
    check_auth(opts.username, opts.password)
    try:
        if opts.listfilters:
            idx=1
            for f in get_filters():
                print "%d. %s (Owner: %s)" % (idx,  f["name"], colorfunc(f["author"],"green"))
                idx+=1
        elif opts.listtypes:
            print "Priorities:"
            for el in  get_issue_priority(None):
                print el["name"], ":", el["description"]
            print
            print "Issue Types:"
            for el in  get_issue_type(None):
                print el["name"], ":", el["description"]
        else:

            if opts.issue_type:
                project = opts.jira_project
                if args:
                    description = " ".join(args)
                else:
                    description = default_editor_text
                print format_issue ( create_issue ( project, opts.issue_type, opts.issue_title,  description, opts.issue_priority ), 0, opts.format)
            elif opts.comment:
                if not opts.jira_id:
                    parser.error("specify the jira to comment on")
                print add_comment(opts.jira_id, " ".join(args) if args else default_editor_text)
            elif opts.search:
                issues = search_issues ( opts.search )
                for issue in issues:
                    mode = 0 if not opts.verbose else 1
                    mode = -1 if opts.oneline else mode
                    print format_issue( issue, mode, opts.format )
            else:
                # otherwise we're just showing the jira.
                # maybe by filter
                if opts.filter:
                    for f in opts.filter.split(","):
                        issues = get_issues_from_filter(f)
                        for issue in issues:
                            mode = 0 if not opts.verbose else 1
                            mode = -1 if opts.oneline else mode
                            print format_issue( issue, mode , opts.format)
                else:
                    if not (opts.jira_id or args):
                        parser.error("jira id must be provided")
                    if args:
                        for arg in args:
                            issue = get_jira(arg)
                            mode = 0 if not opts.verbose else 1
                            mode = -1 if opts.oneline else mode
                            print format_issue( issue, mode , opts.format)
                    if opts.jira_id:
                        issue = get_jira(opts.jira_id)
                        print format_issue( issue, 0  if not opts.verbose else 1, opts.format)
    except Exception, e:
        parser.error(colorfunc(str(e), "red"))

if __name__ == "__main__":
    main()

