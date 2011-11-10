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

def get_issue_type(type):
    if os.path.isfile(os.path.expanduser("~/.jira-cli/types.pkl")):
        issue_types = pickle.load(open(os.path.expanduser("~/.jira-cli/types.pkl"),"rb"))
    else:
        issue_types = jiraobj.jira1.getIssueTypes(token)
        pickle.dump(issue_types,  open(os.path.expanduser("~/.jira-cli/types.pkl"),"wb"))

    if not type:
        return issue_types
    else:
        for t in issue_types:
            if t["name"].lower() == type:
                return t["id"]


def get_issue_priority(priority):
    if os.path.isfile(os.path.expanduser("~/.jira-cli/priorities.pkl")):
        issue_priorities = pickle.load(open(os.path.expanduser("~/.jira-cli/priorities.pkl"),"rb"))
    else:
        issue_priorities = jiraobj.jira1.getPriorities(token)
        pickle.dump(issue_priorities,  open(os.path.expanduser("~/.jira-cli/priorities.pkl"),"wb"))

    if not priority:
        return issue_priorities
    else:
        for t in issue_priorities:
            if t["name"].lower() == type:
                return t["id"]

def check_auth():
    global jiraobj, token, jirabase

    setup_home_dir()
    if os.path.isfile(os.path.expanduser("~/.jira-cli/base")):
        jirabase = open(os.path.expanduser("~/.jira-cli/base")).read().strip()
    else:
        jirabase = raw_input("please enter the base url for your jira instance:")
        open(os.path.expanduser("~/.jira-cli/base"),"w").write(jirabase)

    if os.path.isfile(os.path.expanduser("~/.jira-cli/auth")):
        token = open(os.path.expanduser("~/.jira-cli/auth")).read()
    try:
        jiraobj = xmlrpclib.ServerProxy("%s/rpc/xmlrpc" % jirabase )
        jiraobj.jira1.getIssueTypes(token)
    except Exception, e:
        username = raw_input("enter username:")
        token = jiraobj.jira1.login(username,  getpass.getpass("enter password:"))
        open(os.path.expanduser("~/.jira-cli/auth"),"w").write(token)

def format_issue( issue , mode = 0 ):
    fields = {}
    if mode >= 0:
        # minimal
        fields["issue"] = issue["key"]
        fields["reporter"] = issue["reporter"]
        fields["assignee"] = issue.setdefault("assignee","")
        fields["summary"] = issue["summary"]
        fields["link"] = "%s/browse/%s" % ( jirabase, issue["key"])
    if mode >= 1:
        fields["description"] = issue["description"]
    if mode < 0:
        global colorfunc
        if not sys.stdout.isatty():
            colorfunc = lambda x,y:str(x)
        return colorfunc(issue["key"],"red") +" "+ issue["summary"] + colorfunc(" < %s/browse/%s > " % (jirabase, issue["key"]), "green")

    return "\n".join( " : ".join((k.ljust(20),v)) for k,v in fields.items() ) + "\n"



def get_jira( jira_id ):
    """
    """
    return jiraobj.jira1.getIssue( token, jira_id )

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
view jira: jiracli BE-193
add a comment: jiracli -j BE-193 -c "i am sam"
create a new issue: jiracli -n bug -p BE -t "i am sam" "and this is my long description
ending
here"
"""
    parser = optparse.OptionParser()
    parser.usage = example_usage
    parser.add_option("-c","--comment",dest="comment", help="comment on a jira")
    parser.add_option("-j","--jira-id", dest="jira_id",help="issue id")
    parser.add_option("-n","--new", dest = "issue_type", help="create a new issue with given title")
    parser.add_option("-t","--title", dest = "issue_title", help="new issue title")
    parser.add_option("-p","--project",dest="jira_project", help="the jira project to act on")
    parser.add_option("","--one-line",dest="oneline", help="print only one line of info", action="store_true")
    parser.add_option("","--list-jira-types",dest="listtypes", help="print out the different jira 'types'", action="store_true")
    parser.add_option("-v",dest="verbose", action="store_true", help="print extra information")
    
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
                print format_issue ( create_issue ( project, opts.issue_type, opts.issue_title,  description ), 0)
            elif opts.comment:
                if not opts.jira_id:
                    parser.error("specify the jira to comment on")
                print add_comment(opts.jira_id, opts.comment)

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
        parser.error(str(e))

if __name__ == "__main__":
    main()

