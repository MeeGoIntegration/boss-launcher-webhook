from __future__ import absolute_import

import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'webhook_launcher.settings'

from webhook_launcher.celery import app
from webhook_launcher.app.payload import get_payload

from osc import conf, core
from StringIO import StringIO

@app.task
def handle_webhook(workitem):
    """Handle POST request to a webhook."""

    payload = get_payload(workitem["payload"]["payload"])
    payload.handle()

    return workitem

@app.task
def relay_webhook(workitem):
    """Relay webhook POST request to task queue."""

    payload = get_payload(workitem["payload"]["payload"])
    payload.relay()

    return workitem


service_template = """
<services>
<service name="tar_git">
  <param name="url">%(repourl)s</param>
  <param name="branch">%(branch)s</param>
  <param name="revision">%(revision)s</param>
  <param name="token">%(token)s</param>
  <param name="debian">%(debian)s</param>
  <param name="dumb">%(dumb)s</param>
</service>
</services>
"""

@app.task
def trigger_service(workitem):

    f = workitem["payload"]
    project = f["project"]
    package = f["package"]

    params = {}
    for p in ["repourl", "branch", "revision", "token", "debian", "dumb"]:
        params[p] = f.get(p, "")

    conf.get_config()
    apiurl = conf.config["apiurl_aliases"].get(f["ev"]["namespace"], conf.config["apiurl"])

    try:
        core.show_files_meta(apiurl, str(project), str(package), expand=False, meta=True)
    except Exception, exc:
        data = core.metatypes['pkg']['template']
        data = StringIO(data % { "name" : str(package), "user" : conf.config['api_host_options'][apiurl]['user'] }).readlines()
        u = core.makeurl(apiurl, ['source', str(project), str(package), "_meta"])
        x = core.http_PUT(u, data="".join(data))

    service = service_template % params
    core.http_PUT(core.makeurl(apiurl, ['source', project, package, "_service"]),
                  data=service)
    return workitem

@app.task
def create_branch(workitem):

    f = workitem["payload"]
    project = f["project"]
    package = f["package"]
    pr_id = f["pr"]["id"]

    conf.get_config()
    apiurl = conf.config["apiurl_aliases"].get(f["ev"]["namespace"], conf.config["apiurl"])
    # move to build system support classes
    core.branch_pkg(apiurl, project, package, nodevelproject=True, target_project=project+":"+pr_id, target_package=package, return_existing=True, force=True, add_repositories=True)
    return workitem

# temporary placeholder until BuildService model has support for OBS and other build systems
def obs_create_request(apiurl, options_list, description, comment, supersede = False, **kwargs):

    import xml.etree.cElementTree as ElementTree
    commentElement = ElementTree.Element("comment")
    commentElement.text = comment

    state = ElementTree.Element("state")
    state.set("name", "new")
    state.append(commentElement)

    request = core.Request()
    request.description = description
    request.state = core.RequestState(state)

    supsersedereqs = []
    for item in options_list:
        if item['action'] == "submit":
            request.add_action(item['action'],
                               src_project = item['src_project'],
                               src_package = item['src_package'],
                               tgt_project = item['tgt_project'],
                               tgt_package = item['tgt_package'],
                               src_rev = core.show_upstream_rev(apiurl, item['src_project'], item['src_package']),
                               **kwargs)

            if supersede == True:
                supsersedereqs.extend(core.get_exact_request_list(apiurl, item['src_project'],
                                                                  item['tgt_project'], item['src_package'],
                                                                  item['tgt_package'], req_type='submit',
                                                                  req_state=['new','review', 'declined']))
    request.create(apiurl)

    if supersede == True and len(supsersedereqs) > 0:
        processed = []
        for req in supsersedereqs:
            if req.reqid not in processed:
                processed.append(req.reqid)
                print "req.reqid: %s - new ID: %s\n"%(req.reqid, request.reqid)
                core.change_request_state(apiurl, req.reqid,
                                          'superseded',
                                          'superseded by %s' % request.reqid,
                                          request.reqid)

    return request

@app.task
def auto_promote(workitem):

    f = workitem["payload"]
    project = f["project"]
    package = f["package"]
    pr_id = f["pr"]["id"]

    conf.get_config()
    apiurl = conf.config["apiurl_aliases"].get(f["ev"]["namespace"], conf.config["apiurl"])

    actions = [{"action" : "submit", "src_project" : project+":"+pr_id, "src_package" : package,
                        "tgt_project" : project, "tgt_package" : package}]
    comment = ""
    result = obs_create_request(apiurl, options_list=actions, description="", comment=comment, supersede=True, opt_sourceupdate="cleanup")
    return workitem

