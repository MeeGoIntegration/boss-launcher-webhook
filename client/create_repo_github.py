#!/usr/bin/python
# Copyright (C) 2013 Jolla Ltd.
# Contact: Islam Amer <thomas.perl@jollamobile.com>
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

# Create a repository on Github and set up webhooks for it
# Assumption: github credentials (api.github.com) in ~/.netrc
# Dependencies: curl

import sys
import json
import subprocess
import time

WEBHOOK_TARGETS = [
#    'https://webhook.merproject.org/webhook/',
    'https://webhook.jollamobile.com/webhook/',
]

if len(sys.argv) != 3:
    print 'Usage: {program} <orga> <repository>'.format(program=sys.argv[0])
    sys.exit(1)

orga, repository = sys.argv[1:]
url = ''

# GitHub API imposes a rate limit
# https://developer.github.com/v3/#rate-limiting
wait = lambda: time.sleep(2)
curl = lambda *args: ['curl', '--show-error', '--fail', '--netrc', '--silent'] + list(args)
fmt = lambda x: x.format(orga=orga, repository=repository, url=url)

cmd = lambda *args: json.loads(subprocess.check_output(*args, stderr=subprocess.STDOUT))
get = lambda url: cmd(curl(fmt(url)))
post = lambda url, data: cmd(curl('--request', 'POST', '--data', json.dumps(data), fmt(url)))
patch = lambda url, data: cmd(curl('--request', 'PATCH', '--data', json.dumps(data), fmt(url)))

# GitHub API uses paginated lists so we can't get a full list "quickly"
# https://developer.github.com/v3/#pagination
try:
    repo = get('https://api.github.com/repos/{orga}/{repository}')
    print fmt('Repository exists: {repository}')
except subprocess.CalledProcessError, exc:
    if "404 Not Found" in exc.output:
        print fmt('Creating repository: {repository}')
        post('https://api.github.com/orgs/{orga}/repos', {'name': repository})
    else:
        print exc.output
        sys.exit(1)

wait()

# Get list of existing web hooks for that repository
hooks = get('https://api.github.com/repos/{orga}/{repository}/hooks')
existing_hooks = {}
for hook in hooks:
    if hook['name'] == 'web':
        existing_hooks[hook['config']['url']] = hook['id']

# Create all required web hooks if they don't exist yet
for url in WEBHOOK_TARGETS:
    config = {'name': 'web', 'active': True, 
              'config': {'url': url, 'content_type': 'json', },
              'events': ['push', 'pull_request'], }
    if url not in existing_hooks:
        print fmt('Adding hook: {url}')
        post('https://api.github.com/repos/{orga}/{repository}/hooks', config)
        wait()
    else:
        print fmt('Updating existing hook: {url}')
        patch('https://api.github.com/repos/{orga}/{repository}/hooks/%s' % existing_hooks[url], config)
        wait()
