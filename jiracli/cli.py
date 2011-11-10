import getpass
import os
import optparse
import xmlrpclib
import collections
import pickle
import sys
from termcolor import colored as colorfunc

jiraobj = None
token = None
type_dict = {}
jirabase=None

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

def check_auth():
    global jiraobj, token, jirabase

    setup_home_dir()
    if os.path.isfile(os.path.expanduser("~/.jira-cli/config")):
        jirabase = open(os.path.expanduser("~/.jira-cli/config")).read().strip()
    else:
        jirabase = raw_input("base url for your jira instance (e.g http://issues.apache.org/jira):")
        open(os.path.expanduser("~/.jira-cli/config"),"w").write(jirabase)

    if os.path.isfile(os.path.expanduser("~/.jira-cli/auth")):
        token = open(os.path.expanduser("~/.jira-cli/auth")).read()
    try:
        jiraobj = xmlrpclib.ServerProxy("%s/rpc/xmlrpc" % jirabase )
        jiraobj.jira1.getIssueTypes(token)
    except Exception, e:
        def _login():

            username = raw_input("enter username:")
            try:
                return jiraobj.jira1.login(username,  getpass.getpass("enter password:"))
            except:
                print("username or password incorrect, try again.")
                return _login()
        token = _login()
        open(os.path.expanduser("~/.jira-cli/auth"),"w").write(token)

def format_issue( issue , mode = 0 ):
    fields = {}
    global colorfunc
    color=True
    status_color="blue"
    status_string = get_issue_status ( issue.setdefault("status","1")).lower()
    if status_string in ["resolved","closed"]:
        status_color="green"
    elif status_string in ["open","unassigned","reopened"]:
        status_color="red"
    if not sys.stdout.isatty():
        colorfunc = lambda *a:str(a[0])
        color=False
    
    
    
    try:
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
            fields["description"] = issue["description"]
        if mode < 0:
            url_str = colorfunc("%s/browse/%s" % (jirabase, issue["key"]), "white", attrs=["underline"])
            ret_str = colorfunc(issue["key"],status_color) +" "+ issue["summary"] + " " + url_str
            if not color:
                ret_str += "[%s]" % get_issue_status(issue["status"]) + issue["status"]
            return ret_str
        return "\n".join( " : ".join((k.ljust(20),v)) for k,v in fields.items() ) + "\n"
    except Exception,e:
            return "%s: Not found" % issue["key"]


def get_jira( jira_id ):
    """
    """
    try:
        return jiraobj.jira1.getIssue( token, jira_id )
    except:
        return {"key": jira_id }



def add_comment( jira_id, comment ):
    res = jiraobj.jira1.addComment( token, jira_id, comment )
    if res:
        return "%s added to %s" % (comment, jira_id)
    else:
        return "failed to add comment to %s" % jira_id

def create_issue ( project, type=0, summary="", description="" , priority="Major"):
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
    parser.add_option("-c","--comment",dest="comment", help="comment on a jira")
    parser.add_option("-j","--jira-id", dest="jira_id",help="issue id")
    parser.add_option("-n","--new", dest = "issue_type", help="create a new issue with given title")
    parser.add_option("","--priority", dest = "issue_priority", help="priority of new issue", default="minor")
    parser.add_option("-t","--title", dest = "issue_title", help="new issue title")
    parser.add_option("-p","--project",dest="jira_project", help="the jira project to act on")
    parser.add_option("","--oneline",dest="oneline", help="print only one line of info", action="store_true")
    parser.add_option("","--list-jira-types",dest="listtypes", help="print out the different jira 'types'", action="store_true")
    parser.add_option("-v",dest="verbose", action="store_true", help="print extra information")
    parser.add_option("-s","--search",dest="search", help="search criteria" )
    
    opts, args = parser.parse_args()
    check_auth()
    try:
        if opts.listtypes:
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
                    description = args[0]
                else:
                    description = ""
                print format_issue ( create_issue ( project, opts.issue_type, opts.issue_title,  description, opts.issue_priority ), 0)
            elif opts.comment:
                if not opts.jira_id:
                    parser.error("specify the jira to comment on")
                print add_comment(opts.jira_id, opts.comment)
            elif opts.search:
                issues = search_issues ( opts.search )
                for issue in issues:
                    mode = 0 if not opts.verbose else 1
                    mode = -1 if opts.oneline else mode
                    print format_issue( issue, mode )
            else:
                # otherwise we're just showing the jira.
                if not (opts.jira_id or args):
                    parser.error("jira id must be provided")
                if args:
                    for arg in args:
                        issue = get_jira(arg)
                        mode = 0 if not opts.verbose else 1
                        mode = -1 if opts.oneline else mode
                        print format_issue( issue, mode )
                if opts.jira_id:
                    issue = get_jira(opts.jira_id)
                    print format_issue( issue, 0  if not opts.verbose else 1)
    except Exception, e:
        import traceback
        traceback.print_exc()
        parser.error(str(e))

if __name__ == "__main__":
    main()

