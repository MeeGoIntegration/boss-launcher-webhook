#!/usr/bin/python -tt
import sys
import os
import json
import subprocess
from optparse import OptionParser

WEBHOOK = 'https://webhook.jollamobile.com/webhook/api/webhookmappings/'

def geturl(*arg):
    """ Convenience funtion to create url with trailing slash. Joins arguments together.
    """
    path = os.path.join(WEBHOOK, *arg)
    # make sure path has trailins slash
    if not path.endswith('/'):
        path = os.path.join(path, '')
    return path

json_header = "Content-Type: application/json"
curl = lambda *args: ['curl', '--header', json_header , '--show-error',  '--netrc', '--silent'] + list(args)
cmd = lambda *args: json.loads(subprocess.check_output(*args, stderr=subprocess.STDOUT))
cmd_no_reply = lambda *args: subprocess.check_call(*args)
get = lambda url: cmd(curl(url))
put = lambda url: cmd(curl('--request', 'PUT', url))
delete = lambda url: cmd_no_reply(curl('--request', 'DELETE', url))
post = lambda url, data: cmd(curl('--request', 'POST', '--data', json.dumps(data), url))
patch = lambda url, data: cmd(curl('--request', 'PATCH', '--data', json.dumps(data), url))

def parseArgs():
    usage = """
    list all hooks:
	./webhook_client --list
        or filter a bit
        ./webhook_client --list --filter-project=foo:bar

    show specific webhook:
	./webhook_client.py --id <id>
        passing -v or --verbose flag will output all json fields.

    modify:
	./webhook_client: --id --modify --<field_to_modify> <value>
        e.g. --id 999 --modify --build false

    delete:
	./webhook_client.py --id <id> --delete

    trigger webhook:
	./webhook_client.py --id <id> --trigger

    """
    parser = OptionParser(version = "webhook_client 0.1", usage=usage)

    # listing existing webhooks:
    parser.add_option('--list', action='store_true', dest='list')
    parser.add_option('--filter-user', action='store', dest='filter_user')
    parser.add_option('--filter-project', action='store', dest='filter_prj')
    parser.add_option('--filter-package', action='store', dest='filter_pkg')
    parser.add_option('--filter-build', action='store', dest='filter_build')
    parser.add_option('--filter-repourl', action='store', dest='filter_repourl')
    parser.add_option('-v', '--verbose', action='store_true', dest='verbose')

    # create new
    parser.add_option('--create', action='store_true', dest='create')

    # show / modify / delete spesific hook
    parser.add_option('--id', action='store', dest='hook_id')
    parser.add_option('--delete', action='store_true', dest='delete_hook')
    parser.add_option('--modify', action='store_true', dest='modify')

    # trigger webhook
    parser.add_option('--trigger', action='store_true', dest='trigger')

    # fields available for modification
    parser.add_option('--repourl', action='store', dest='repourl')
    parser.add_option('--branch', action='store', dest='branch')
    parser.add_option('--project', action='store', dest='project')
    parser.add_option('--package', action='store', dest='package')
    parser.add_option('--build', action='store', dest='build')
    parser.add_option('--notify', action='store', dest='notify')
    parser.add_option('--token', action='store', dest='token')
    parser.add_option('--comment', action='store', dest='comment')
    parser.add_option('--tag', action='store', dest='tag')
    parser.add_option('--revision', action='store', dest='revision')
    parser.add_option('--obs', action='store', dest='obs')

    (opts, _) = parser.parse_args()
    return opts

webhook_print_template = "%(id)5s | %(project)10s | %(package)30s | %(branch)10s | %(repourl)10s"
def _print_header():
    fields = {
        "id" : "Id",
        "package": "Package",
        "project" : "Project",
        "repourl" : "Repourl",
        "branch" : "Branch",
        }
    print webhook_print_template % fields
    print "-"*80

def _print_entry(data, verbose=False):
    if verbose:
        print json.dumps(data, indent=4)
    else:
        print webhook_print_template % data

def print_list(opts):
    url = geturl()
    query_url = ""
    if opts.filter_prj:
        query_url += "project=%s&" % opts.filter_prj
    if opts.filter_pkg:
        query_url += "package=%s&" % opts.filter_pkg
    if opts.filter_user:
        query_url += "user__username=%s&" % opts.filter_user
    if opts.filter_repourl:
        query_url += "repourl=%s&" % opts.filter_repourl
    if opts.filter_build:
        # rest of the options work with lower case false/true
        # so make also this to work like that. Filtering needs
        # True / False to work
        if opts.filter_build.lower() == "false":
            build_flag = "False"
        elif opts.filter_build.lower() == "true":
            build_flag = "True"
        if build_flag:
            query_url += "build=%s&" % build_flag
    if query_url:
        url += "?" + query_url

    hooklist = get(url)
    if not opts.verbose:
        _print_header()
    for row in hooklist:
        _print_entry(row, verbose=opts.verbose)

def show_hook(hook_id, verbose=False):
    url = geturl(hook_id)
    webhook = get(url)
    detail = webhook.get('detail', None)
    if detail:
        print detail
    else:
        _print_entry(webhook, verbose=verbose)

def create_hook(opts):
    data = {}
    for k,v in vars(opts).items():
        if 'create' in k: # strip away the creation argument
            continue
        if v:
            data[k] = v
    url = geturl()
    return post(url, data)

def patch_hook(opts):

    data = {}
    hook_id = opts.hook_id
    url = geturl(hook_id)

    for k, v in vars(opts).items():
        if 'modify' in k or 'hook_id' in k or 'verbose' in k:
            continue
        if not v: continue
        # special case for last seen revision:
        if 'tag' in k or 'revision' in k:
            if not 'lsr' in data.keys():
                data['lsr'] = {}
            data['lsr'][k] = v
        elif v:
            data[k] = v

    return patch(url, data)

def delete_hook(hook_id):
    url = geturl(hook_id)
    webhook = delete(url)
    return webhook

def trigger_hook(hook_id):
    hook_id = opts.hook_id
    url = geturl(hook_id)
    return put(url)

if __name__ == "__main__":

    opts = parseArgs()

    if opts.create:
        if opts.hook_id:
            print "Invalid arguments. Cannot have '--id' together with '--create'"
            sys.exit(1)
        if opts.delete_hook:
            print "Invalid arguments. Cannot have '--delete' together with '--create'"
            sys.exit(1)
        if opts.modify:
            print "Invalid arguments. Cannot have '--create' and '--modify' together"
            sys.exit(1)
        if not opts.repourl or not opts.branch or not opts.project or not opts.package or not opts.obs or not opts.revision:
            print "mandatory arguments with --create: '--repourl', '--branch', '--project',  '--package', '--obs', '--revision'"
            sys.exit(1)
        created = create_hook(opts)
        print json.dumps(created, indent=4)
        sys.exit(0)

    if opts.delete_hook:
        if not opts.hook_id:
            print "Need to give webhook id '--id' together with '--delete'"
            sys.exit(1)
        delete_hook(opts.hook_id)
        sys.exit(0)

    if opts.modify:
        if opts.create or opts.delete_hook or opts.trigger:
            print  "Invalid arguments. Cannot have '--create', '--delete', or '--trigger' together with modify"
            sys.exit(1)
        hook = patch_hook(opts)
        print json.dumps(hook, indent=4)
        sys.exit(0)

    if opts.trigger:
        if not opts.hook_id:
            print "Give hook id to trigger"
            sys.exit(1)
        hook = trigger_hook(opts.hook_id)
        print json.dumps(hook, indent=4)
        sys.exit(0)

    if opts.list:
        print_list(opts)
        sys.exit(0)

    if opts.hook_id:
        show_hook(opts.hook_id, verbose=opts.verbose)
        sys.exit(0)
