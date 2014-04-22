#!/bin/bash
# Copyright (C) 2014 Jolla Ltd.
# Contact: Islam Amer <islama.amer@jollamobile.com>
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

# Convenience script for initial setup of a subtree based packaging repository
# Dependencies: git subtree
#set -x
set -e

usage () {

  echo "$0 <tarball> <upstream reference (tag or branch)> <subtree prefix>"
  echo "$0 <submodule clone url> <upstream reference (tag or branch)>"
  exit 1

}

test $# -ge 2 || usage
test -d .git || ( echo "Current working directory is not a git repository" ; exit 1 )

git commit --allow-empty -m "initial empty commit"

if test -f "$1" ; then
  git checkout -b upstream || git checkout upstream
  tar -xvf $1 --strip-components=1
  git add -A
  git commit -a -m "import from upstream tarball $(basename $1)"
  if test -n "$2"; then
    git tag upstream/$2
  fi
  if test -x $(which pristine-tar); then
    pristine-tar commit $1
  fi
  git checkout master
  git clean -fdx
  if test -n "$3"; then
    git subtree add --squash --prefix=$3 upstream
  else
    echo "git subtree add --squash --prefix=<name> upstream"
  fi
  
else

  git submodule add $1 upstream
  pushd upstream
    git checkout -B reference-branch $2
  popd
  git commit -a -m "add upstream submodule"

  git remote add -f --no-tags upstream upstream
  git branch reference-branch upstream/reference-branch

  git subtree add --squash --prefix=$(basename $1 .git) upstream reference-branch

fi

mkdir -p rpm
