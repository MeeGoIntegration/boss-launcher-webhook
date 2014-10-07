#!/usr/bin/python
import json
import sys

old_file=sys.argv[1]
new_file=sys.argv[2]

try:
    old = json.loads(open(old_file).read())
except Exception,e:
    print "%s is not valid json : %s" % (old_file, e)
    sys.exit(1)
    
try:
    new = json.loads(open(new_file).read())
except Exception,e:
    print "%s is not valid json : %s" % (new_file, e)
    sys.exit(1)

# We consider an update needed if any of these don't match
keys = ["repourl", "branch", "project", "package", "token", "debian", "dumb", "notify", "build", "comment"]
errors=[]

for key in keys:
    if key in old:
        if key in new:
            if old[key] != new[key]:
                errors.append("%s: differs (%s != %s)" %
                    (key, old[key], new[key]))
        else:
            errors.append("%s: in %s, not %s" % (key, old_file, new_file))
    else:
        if key in new:
            errors.append("%s: in %s, not %s" % (key, new_file, old_file))

if len(errors) > 0:
    print "Don't match:"
    for e in errors:
        print " %s" %e
    sys.exit(1)
else:
    sys.exit(0)

