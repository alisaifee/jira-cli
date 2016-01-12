import getpass
import logging
import re
import os
import optparse
import tempfile
import socket
import pickle
import sys
from six.moves import urllib

from suds.client import Client
from suds import WebFault
from termcolor import colored as colorfunc

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.CRITICAL)

jiraobj = None
token = None
type_dict = {}
jirabase=None
color = True
if not sys.stdout.isatty():
    colorfunc = lambda *a,**k:str(a[0]).encode('utf-8')
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
        issue_types = jiraobj.service.getIssueTypes(token)
        issue_types = [dict(k) for k in issue_types]
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
        issue_stats = jiraobj.service.getStatuses(token)
        issue_stats = [dict(k) for k in issue_stats]
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
        issue_priorities = jiraobj.service.getPriorities(token)
        issue_priorities = [dict(k) for k in issue_priorities]
        pickle.dump(issue_priorities,  open(os.path.expanduser("~/.jira-cli/priorities.pkl"),"wb"))

    if not priority:
        return issue_priorities
    else:
        for t in issue_priorities:
            if t["name"].lower() == priority:
                return t["id"]

def search_issues ( criteria ):
    return jiraobj.service.getIssuesFromTextSearch(token, criteria )

def search_issues_jql( query, limit=1024):
    return jiraobj.service.getIssuesFromJqlSearch(token, query, limit)

def search_issues_with_project ( project, criteria, numresult):
    return jiraobj.service.getIssuesFromTextSearchWithProject(token, [project], criteria, numresult)


def check_auth(username, password):
    def _login(u,p):
        username,password = u,p
        if not u:
            sys.stderr.write("enter username:")
            username = sys.stdin.readline().strip()
        if not p:
            password = getpass.getpass("enter password:")
        try:
            return jiraobj.service.login(username,  password)
        except:
            print >> sys.stderr, colorfunc("username or password incorrect, try again.", "red")
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
            urllib.request.urlopen('%s/rpc/soap/jirasoapservice-v2?wsdl' % jirabase)
            jiraobj = Client('%s/rpc/soap/jirasoapservice-v2?wsdl' % jirabase)
            # lame ping method
            jiraobj.service.getIssueTypes()
        except (socket.gaierror, IOError):
            print >> sys.stderr, colorfunc("invalid url %s. Please provide the correct url for your jira installation" % jirabase, "red")
            return _validate_jira_url()
        except WebFault:
            open(os.path.expanduser("~/.jira-cli/config"),"w").write(jirabase)
        return None


    if os.path.isfile(os.path.expanduser("~/.jira-cli/config")):
        jirabase = open(os.path.expanduser("~/.jira-cli/config")).read().strip()
    _validate_jira_url( jirabase )
    if os.path.isfile(os.path.expanduser("~/.jira-cli/auth")):
        token = open(os.path.expanduser("~/.jira-cli/auth")).read()
    try:
        jiraobj = Client("%s/rpc/soap/jirasoapservice-v2?wsdl" % jirabase)
        jiraobj.service.getIssueTypes(token)
    except Exception:
        token = _login(username,password)
        open(os.path.expanduser("~/.jira-cli/auth"),"w").write(token)

def format_issue( issue , mode = 0, formatter=None, comments_only=False):
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
                ret_str = ret_str.replace(k, str(issue.setdefault(v.lower(),"")))
        return ret_str

    if mode >= 0:
        # minimal
        fields["issue"] = issue["key"]
        fields["status"] = colorfunc( get_issue_status ( issue["status"] )
                                    , status_color )
        fields["reporter"] = issue.setdefault("reporter","")
        fields["assignee"] = issue.setdefault("assignee","")
        fields["summary"] = issue.setdefault("summary","")
        fields["link"] = colorfunc( "%s/browse/%s" % ( jirabase, issue["key"]), "white",attrs=["underline"])
    if mode >= 1 or comments_only:
        fields["description"] = issue.setdefault("description","")
        fields["priority"] = get_issue_priority( issue.setdefault("priority",""))
        fields["type"] = get_issue_type( issue.setdefault("type","") )
        comments = get_comments ( issue["key"] )
        fields["comments"] = "\n"
        for comment in comments:
            comment_str =  comment["body"].strip()
            fields["comments"] += "%s %s : %s\n" % ( colorfunc(comment["created"], "blue"), colorfunc(comment["author"], "green"), comment_str )
    if comments_only:
        return fields["comments"].strip()
    elif mode < 0:
        url_str = colorfunc("%s/browse/%s" % (jirabase, issue["key"]), "white", attrs=["underline"])
        ret_str = colorfunc(issue["key"],status_color) +" "+ issue.setdefault("summary","") + " " + url_str
        if not color:
            ret_str += " [%s] " % get_issue_status(issue["status"])
        return ret_str
    for k,v in fields.items():
        if not v:
            fields[k] = ""
    return "\n".join( " : ".join((k.ljust(20),v)) for k,v in fields.items() ) + "\n"


def get_jira( jira_id ):
    """
    """
    try:
        return jiraobj.service.getIssue( token, jira_id )
    except:
        return {"key": jira_id }

def get_filters( ):
    saved = jiraobj.service.getSavedFilters( token )
    favorites = jiraobj.service.getFavouriteFilters (token)

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
        return jiraobj.service.getIssuesFromFilter ( token, fid )
    return []

def get_comments ( jira_id ):
    return jiraobj.service.getComments ( token , jira_id )

def add_comment( jira_id, comment ):
    if comment == default_editor_text:
        comment = get_text_from_editor(default_editor_text % ("comment"))
    res = jiraobj.service.addComment( token, jira_id, comment )
    if res:
        return "%s added to %s" % (comment, jira_id)
    else:
        return "failed to add comment to %s" % jira_id

def create_issue ( project, type=0, summary="", description="" , priority="Major", assignee="", reporter=""):
    if description == default_editor_text:
        description = get_text_from_editor(default_editor_text % ("new issue"))

    issue =  {"project":project.upper(), "type": get_issue_type(type), "summary":summary, "description":description, "priority": get_issue_priority(priority), "assignee": assignee, "reporter": reporter}
    return jiraobj.service.createIssue( token, issue )


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
    parser.add_option("-c", "--comment", dest="comment", help="comment on a jira", action="store_true")
    parser.add_option("", "--comments-only", dest="commentsonly", help="show only the comments for a jira",
                      action="store_true")
    parser.add_option("-j", "--jira-id", dest="jira_id", help="issue id")
    parser.add_option("", "--filter", dest="filter",
                      help="filter(s) to use for listing jiras. use a comma to separate multiple filters")
    parser.add_option("-n", "--new", dest="issue_type", help="create a new issue with given title")
    parser.add_option("", "--priority", dest="issue_priority", help="priority of new issue", default="minor")
    parser.add_option("-t", "--title", dest="issue_title", help="new issue title")
    parser.add_option("-p", "--project", dest="jira_project", help="the jira project to act on")
    parser.add_option("", "--oneline", dest="oneline", help="print only one line of info", action="store_true")
    parser.add_option("", "--list-jira-types", dest="listtypes", help="print out the different jira 'types'",
                      action="store_true")
    parser.add_option("", "--list-filters", dest="listfilters", help="print out the different jira filters available",
                      action="store_true")
    parser.add_option("-v", dest="verbose", action="store_true", help="print extra information")
    parser.add_option("-s", "--search", dest="search", help="search criteria")
    parser.add_option("", "--search-jql", dest="search_jql", help="JQL expression")
    parser.add_option("-f", "--format", dest="format", default=None, help="""format for outputting information.
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
                print("%d. %s (Owner: %s)" % (idx,  f["name"], colorfunc(f["author"],"green")))
                idx+=1
        elif opts.listtypes:
            print("Priorities:")
            for el in  get_issue_priority(None):
                print(el["name"], ":", el["description"])
            print()
            print("Issue Types:")
            for el in  get_issue_type(None):
                print(el["name"], ":", el["description"])
        else:

            if opts.issue_type:
                project = opts.jira_project
                if args:
                    description = " ".join(args)
                else:
                    description = default_editor_text
                print(format_issue ( dict(create_issue ( project, opts.issue_type, opts.issue_title,  description, opts.issue_priority) ), 0, opts.format))
            elif opts.comment:
                if not opts.jira_id:
                    parser.error("specify the jira to comment on")
                print(add_comment(opts.jira_id, " ".join(args) if args else default_editor_text))
            elif opts.search or opts.search_jql:
                project = opts.jira_project
                if (project is None):
                    issues = search_issues ( opts.search ) if opts.search else search_issues_jql(opts.search_jql)
                else:
                    jira_max_int = pow(2,31)-1
                    issues = search_issues_with_project( project, opts.search, jira_max_int)
                for issue in issues:
                    mode = 0 if not opts.verbose else 1
                    mode = -1 if opts.oneline else mode
                    print(format_issue( dict(issue), mode, opts.format))
            else:
                # otherwise we're just showing the jira.
                # maybe by filter
                if opts.filter:
                    for f in opts.filter.split(","):
                        issues = get_issues_from_filter(f)
                        for issue in issues:
                            mode = 0 if not opts.verbose else 1
                            mode = -1 if opts.oneline else mode
                            print(format_issue( dict(issue), mode , opts.format, opts.commentsonly))
                else:
                    if not (opts.jira_id or args):
                        parser.error("jira id must be provided")
                    if args:
                        for arg in args:
                            issue = get_jira(arg)
                            mode = 0 if not opts.verbose else 1
                            mode = -1 if opts.oneline else mode
                            print(format_issue( dict(issue), mode , opts.format, opts.commentsonly))
                    if opts.jira_id:
                        issue = get_jira(opts.jira_id)
                        print(format_issue( dict(issue), 0  if not opts.verbose else 1, opts.format))
    except Exception as e:
        parser.error(colorfunc(str(e), "red"))

if __name__ == "__main__":
    main()

