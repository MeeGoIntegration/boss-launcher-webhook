# Copyright (C) 2013 Jolla Ltd.
# Contact: Islam Amer <islam.amer@jollamobile.com>
# All rights reserved.
# 
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

from django.conf import settings
from django.contrib.auth.models import User

import urlparse
import json
import requests
import os

from webhook_launcher.app.models import (WebHookMapping, LastSeenRevision, RelayTarget, Project, VCSNameSpace, BuildService)

from webhook_launcher.app.tasks import (handle_commit, handle_pr, trigger_build) 
from webhook_launcher.app.misc import bbAPIcall

def get_payload(data):
    """ payload factory function hides the messy details of detecting payload type """

    bburl = "https://bitbucket.org"
    url = None
    klass = Payload
    params = data.get('webhook_parameters', {})
    repo = data.get('repository', None)
    gh_pull_request = data.get('pull_request', None)
    bb_pr_keys = ["pullrequest_created"]
    # https://bitbucket.org/site/master/issue/8340/pull-request-post-hook-does-not-include
    # "pullrequest_merged", "pullrequest_declined","pullrequest_updated"

    #TODO: support more payload types
    key = None
    for key in bb_pr_keys:
        bb_pull_request = data.get(key, None)
        if bb_pull_request:
            break

    if key and bb_pull_request:
        klass = BbPull
        url = urlparse.urljoin(bburl, data[key]['destination']['repository']['full_name']) + '.git'

    elif gh_pull_request:
        # Github pull request event
        klass = GhPull
        url = data['pull_request']['base']['repo']['clone_url']

    elif repo:
        if repo.get('absolute_url', None):
            # bitbucket type payload
            url = repo.get('absolute_url', None)
            canon_url = data.get('canon_url', None)
            if canon_url and url:
                print "bitbucket payload"
                if url.endswith('/'):
                    url = url[:-1]
                url = urlparse.urljoin(canon_url, url)
                if not url.endswith(".git"):
                    url = url + ".git"
                klass = BbPush

        elif repo.get('url', None):
            # github type payload
            url = repo.get('url', None)
            if url:
                print "github payload"
                if not url.endswith(".git"):
                    url = url + ".git"
                klass = GhPush

    return klass(url, params, data)

class Payload(object):

    def __init__(self, url, params, data):

        self.url = url
        self.params = params
        self.data = data

    def create_placeholder(self, repourl, branch, packages=None):
    
        vcsns = VCSNameSpace.find(repourl)
    
        project = None
        if vcsns and vcsns.default_project:
            project = vcsns.default_project.name
        elif settings.DEFAULT_PROJECT:
            project = settings.DEFAULT_PROJECT
    
        if not project:
            return []
    
        if not packages:
            packages = [""]
    
        print "no mappings, create placeholders"
        mapobjs = []
        for package in packages:
            mapobj = WebHookMapping(repourl=repourl, branch=branch,
                                    user=User.objects.get(id=1),
                                    obs=BuildService.objects.all()[0],
                                    notify=False, build=False,
                                    project=project, package=package,
                                    comment="Placeholder")
            mapobj.save()
            mapobjs.append(mapobj)
    
        return mapobjs

    def relay(self, relays=None):

        if not self.url:
            return

        parsed_url = urlparse.urlparse(self.url)
        official_projects = list(set(prj.name for prj in Project.objects.filter(official=True, allowed=True)))
        official_packages = list(set(mapobj.package for mapobj in
                                WebHookMapping.objects.filter(repourl=self.url,
                                project__in=official_projects).exclude(package="")))

        service_path = os.path.dirname(parsed_url.path)
        if not relays:
            relays = list(RelayTarget.objects.filter(active=True,
                                    sources__path=service_path,
                                    sources__service__netloc=parsed_url.netloc))
            if not relays:
                return

        headers = {'content-type': 'application/json'}
        proxies = {}

        if settings.OUTGOING_PROXY:
            proxy = "%s:%s" % (settings.OUTGOING_PROXY, settings.OUTGOING_PROXY_PORT)
            proxies = {"http" : proxy, "https": proxy}

        payload = self.data
        payload["webhook_parameters"]["packages"] = official_packages
        data = json.dumps(payload)
        for relay in relays:
            #TODO: allow uploading self signed certificates and client certificates
            print "Relaying event from %s to %s" % (self.url, relay)
            response = requests.post(relay.url, data=data,
                                     headers=headers, proxies=proxies,
                                     verify=relay.verify_SSL)
            if response.status_code != requests.codes.ok:
                raise RuntimeError("%s returned %s" % (relay, response.status_code))
        

    def handle(self):

        if self.data.get('zen', None) and self.data.get('hook_id', None):
            # Github ping event, do nothing
            print "Github says hi!"
        else:
            print "unknown payload"

class GhPull(Payload):

    def handle(self):

        payload = self.data
        repourl = self.url

        branch = payload['pull_request']['base']['ref']
        data = { "url" : payload['pull_request']['html_url'],
                 "source_repourl" : payload['pull_request']['head']['repo']['clone_url'],
                 "source_branch" : payload['pull_request']['head']['ref'],
                 "username" : payload['pull_request']['user']['login'],
                 "action" : payload['action'],
                 "id" : payload['number'],
             }

        for mapobj in WebHookMapping.objects.filter(repourl=repourl, branch=branch):
            handle_pr(mapobj, data, payload)

class GhPush(Payload):

    def handle(self):

        payload = self.data
        repourl = self.url

        # github performs one POST per ref (tag/branch) touched even if they are pushed together
        if 'ref' not in payload:
            print "This payload has no 'ref' in it. Nothing to do."
            return
        refsplit = payload['ref'].split("/", 2)
        if len(refsplit) > 1:
            reftype, refname = refsplit[1:]
        else:
            print "Couldn't figure out reftype or refname"
            return

        if reftype == "tags":
        # tag
            if 'base_refs' in payload:
                branches = payload['base_refs']
            elif 'base_ref' in payload and not payload['base_ref'] is None:
                branches = [payload['base_ref'].split("/")[2]]
            else:
                # unfortunately github doesn't send info about the branch that an annotated tag is in
                # nor the commit sha1 it points at. The tag itself is enough to tell what to pull and build
                # but we wouldn't know which project / package to trigger
                # try to use the head sha1sum to detect
                print "annotated tag on %s" % repourl
                branches = []

        elif reftype == "heads":
        # commit to branch
            branches = [refname]
        else:
            print "Couldn't use payload"
            return

        print repourl
        print branches
        mapobj = None
        mapobjs = WebHookMapping.objects.filter(repourl=repourl)
        if branches:
            mapobjs = mapobjs.filter(branch__in=branches)
        print mapobjs

        zerosha = '0000000000000000000000000000000000000000'
        # action
        if payload.get('after', '') == zerosha:
            #deleted
            if reftype == "heads":
                for mapobj in mapobjs:
                    # branch was deleted
                    # FIXME: Notify
                    # NOTE: do related objects get removed ?
                    mapobj.delete()
        else:
            #created or changed
            #the head commit is either the branch's HEAD or what the tag is pointing at
            revision = None
            name = None
            emails = set()
            if 'head_commit' in payload:
                revision = payload['head_commit']['id']
                name = payload["pusher"]["name"]
                try:
                    emails.add(payload["head_commit"]["author"]["email"])
                    emails.add(payload["head_commit"]["committer"]["email"])
                except KeyError as e:
                    # do not fail if head_commit does not have "author" or "committer" info
                    pass
            else:
                revision = payload['after']
                name = payload["user_name"]
                for commit in payload.get("commits", []):
                    emails.add(commit["author"]["email"])
                    if len(emails) == 2:
                        break

            if "pusher" in payload:
                emails.add(payload["pusher"]["email"])

            if not revision or not name:
                return

            if not len(mapobjs):
                mapobjs = []
                packages = self.params.get("packages", None)
                for branch in branches:
                    mapobjs.extend(self.create_placeholder(repourl, branch,
                                                           packages=packages))

            notified = False
            for mapobj in mapobjs:
                seenrev, created = LastSeenRevision.objects.get_or_create(mapping=mapobj)
                seenrev.payload = json.dumps(payload)

                if emails:
                    seenrev.emails = json.dumps(list(emails))

                if created or seenrev.revision != revision:
                    if branches:
                        print "%s in %s was not seen before, notify it if enabled" % (revision, mapobj.branch)
                        seenrev.revision = revision

                    else:
                        # annotated tag. only continue if we already had a mapping with a matching
                        # revision
                        continue

                # notify new branch created or commit in branch
                if reftype == "heads":
                    handle_commit(mapobj, seenrev, name, notify=mapobj.notify and not notified)
                    notified = True

                elif reftype == "tags":
                    print "Tag %s for %s in %s/%s, notify and build it if enabled" % (refname, revision, repourl, mapobj.branch)
                    trigger_build(mapobj, name, lsr=seenrev, tag=refname)


class BbPull(Payload):

    def handle(self):

        bburl = "https://bitbucket.org"

        for key, values in self.data.items():
            if not "destination" in values:
                continue
            branch = values['destination']['branch']['name']
            source = urlparse.urljoin(bburl, values['source']['repository']['full_name'])

            data = { "url" : urlparse.urljoin(source + '/', "pull-request/%s" % values['id']),
                     "source_repourl" : source + ".git",
                     "source_branch" : values['source']['branch']['name'],
                     "username" : values['author']['username'],
                     "action" : key.replace("pullrequest_", ""),
                     "id" : values['id'],
                 }

        for mapobj in WebHookMapping.objects.filter(repourl=self.url, branch=branch):
            handle_pr(mapobj, data, self.data)


class BbPush(Payload):

    def handle(self):

        payload = self.data
        repourl = self.url

        mapobj = None
        tips = {}

        #generate pairs of branch : commits in this commit
        for comm in payload['commits']:
            if not comm['branch']:
                print "Dangling commit !" 
            else:
                if not comm['branch'] in tips:
                    tips[comm['branch']] = []
                tips[comm['branch']].append(comm['raw_node'])

        if not len(tips.keys()):
            print "no tips due to empty event, calling api"
            bbcall = bbAPIcall(payload['repository']['absolute_url'])
            bts = bbcall.branches_tags()
            for branch in bts['branches']:
                print branch
                for tag in bts['tags']:
                    print tag
                    if tag['changeset'] == branch['changeset']:
                        print "found tagged branch"
                        tips[branch['name']] = ([branch['changeset']], tag['name'])

        print tips

        for branch, ct in tips.items():
            if isinstance(ct, tuple):
                commits = ct[0]
                tag = ct[1]
            else:
                commits = ct
                tag = None

            mapobjs = WebHookMapping.objects.filter(repourl=repourl, branch=branch)

            if not len(mapobjs):
                packages = self.params.get("packages", None)
                mapobjs = self.create_placeholder(repourl, branch,
                                                  packages=packages)

            notified = False
            for mapobj in mapobjs:
                print "found or created mapping"

                seenrev, created = LastSeenRevision.objects.get_or_create(mapping=mapobj)
                seenrev.payload = json.dumps(payload)
                emails = set()
                for commit in payload["commits"]:
                    emails.add(commit["raw_author"])
                    if len(emails) == 2: break

                if emails:
                    seenrev.emails = json.dumps(list(emails))

                if created or seenrev.revision != commits[-1]:

                    print "%s in %s was not seen before, notify it if enabled" % (commits[-1], branch)
                    seenrev.revision = commits[-1]
                    handle_commit(mapobj, seenrev, payload["user"], notify=mapobj.notify and not notified)
                    notified = True

                else:
                    print "%s in %s was seen before, notify and build it if enabled" % (commits[-1], branch)
                    trigger_build(mapobj, payload["user"], lsr=seenrev, tag=tag)



