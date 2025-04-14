import urlparse

import requests
from django.conf import settings


def normalize_git_url(url):
    dot_git = '.git'
    parsed_url = giturlparse(url)
    git_url = parsed_url.geturl()
    git_url = git_url.rstrip('./\\')

    if not git_url.endswith(dot_git):
        git_url += dot_git
    return git_url


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
        self.base = "https://api.bitbucket.org/2.0"
        self.slug = slug

    def _call_api(self, url):
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
        response = requests.get(
            url,
            proxies=proxies,
            auth=auth,
        )
        response.raise_for_status()
        return response.json()

    def branches(self):
        url = "%s/repositories/%s/refs/branches" % (self.base, self.slug)
        values = []
        while url:
            response = self._call_api(url)
            values.extend(response['values'])
            url = response.get('next')
        return values
