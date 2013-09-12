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
    'https://webhook.merproject.org/webhook/',
]

if len(sys.argv) != 3:
    print 'Usage: {program} <orga> <repository>'.format(program=sys.argv[0])
    sys.exit(1)

orga, repository = sys.argv[1:]
url = ''

wait = lambda: time.sleep(2)
curl = lambda *args: ['curl', '--netrc', '--silent'] + list(args)
fmt = lambda x: x.format(orga=orga, repository=repository, url=url)

cmd = lambda *args: json.loads(subprocess.check_output(*args))
get = lambda url: cmd(curl(fmt(url)))
post = lambda url, data: cmd(curl('--request', 'POST', '--data', json.dumps(data), fmt(url)))

# Get list of existing repositories
repos = get('https://api.github.com/orgs/{orga}/repos')
existing_repos = [repo['name'] for repo in repos]

# Create repository if it doesn't exist yet
if repository not in existing_repos:
    print fmt('Creating repository: {repository}')
    post('https://api.github.com/orgs/{orga}/repos', {'name': repository})
    wait()
else:
    print fmt('Repository exists: {repository}')

# Get list of existing web hooks for that repository
hooks = get('https://api.github.com/repos/{orga}/{repository}/hooks')
existing_hooks = [hook['config']['url'] for hook in hooks if hook['name'] == 'web']

# Create all required web hooks if they don't exist yet
for url in WEBHOOK_TARGETS:
    if url not in existing_hooks:
        print fmt('Adding hook: {url}')
        config = {'name': 'web', 'active': True, 'config': {'url': url}}
        post('https://api.github.com/repos/{orga}/{repository}/hooks', config)
        wait()
    else:
        print fmt('Hook exists: {url}')

