import urlparse

import requests
from django.conf import settings


def giturlparse(repourl):
    parsed = urlparse.urlparse(repourl)
    if not parsed.scheme:
        # if url didn't have scheme prepend default git:// and parse again
        repourl = "git://%s" % repourl
        parsed = urlparse.urlparse(repourl)

    if parsed.netloc.count(":") > 0:
        # if url has : other than the scheme it could be a port or
        # a git service thingie
        try:
            # invalid port raises value error
            port = parsed.port
            repourl = repourl.replace(":%s" % port, "")
            parsed = urlparse.urlparse(repourl)
        except ValueError:
            # in that case replace it with / and reparse
            repourl = "/".join(repourl.rsplit(":", 1))
            parsed = urlparse.urlparse(repourl)

    # finally remove users from the url
    if "@" in parsed.netloc:
        repourl = "%s://%s" % (parsed.scheme, repourl.split("@", 1)[1])
        parsed = urlparse.urlparse(repourl)

    return parsed


def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None


class bbAPIcall(object):
    def __init__(self, slug):
        self.base = "https://api.bitbucket.org/1.0"
        self.slug = slug

    def api_call(self, endpoint, call):
        proxies = {}
        auth = None
        if settings.OUTGOING_PROXY:
            proxy = "%s:%s" % (
                settings.OUTGOING_PROXY,
                settings.OUTGOING_PROXY_PORT
            )
            proxies = {'http': proxy, 'https': proxy}
        if settings.BB_API_USER:
            auth = requests.auth.HTTPBasicAuth(
                settings.BB_API_USER,
                settings.BB_API_PASSWORD
            )
        url = str("/%s/%s/%s" % (endpoint, self.slug, call)).replace("//", "/")
        url = self.base + url
        response = requests.get(
            url,
            verify=False,
            proxies=proxies,
            auth=auth,
        )
        return response.json()

    def branches_tags(self):
        return self.api_call('repositories', 'branches-tags')
