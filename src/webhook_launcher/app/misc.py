from django.conf import settings
import urlparse
import pycurl
import json

def giturlparse(repourl):
    parsed = urlparse.urlparse(repourl)
    if not parsed.scheme:
        #if url didn't have scheme prepend default git:// and parse again
        repourl = "git://%s" % repourl
        parsed = urlparse.urlparse(repourl)

    if parsed.netloc.count(":") > 0:
        #if url has : other than the scheme it could be a port or a git service thingie
        try:
            #invalid port raises value error
            port = parsed.port
            repourl = repourl.replace(":%s" % port, "")
            parsed = urlparse.urlparse(repourl)
        except ValueError, e:
            #in that case replace it with / and reparse
            repourl = "/".join(repourl.rsplit(":", 1))
            parsed = urlparse.urlparse(repourl)

    #finally remove users from the url
    if "@" in parsed.netloc:
        repourl = "%s://%s" % (parsed.scheme, repourl.split("@", 1)[1])
        parsed = urlparse.urlparse(repourl)

    return parsed

def get_or_none(model, **kwargs):
    try:
        return model.objects.get(**kwargs)
    except model.DoesNotExist:
        return None

#TODO: rewrite with requests and addd new API methods
class bbAPIcall(object):
    def __init__(self, slug):
        self.contents = ''
        self.base = "https://api.bitbucket.org/1.0"
        self.slug = slug

    def body_callback(self, buf):
        self.contents += buf

    def api_call(self, endpoint, call):
        c = pycurl.Curl()
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0)
        if settings.OUTGOING_PROXY:
            c.setopt(pycurl.PROXY, settings.OUTGOING_PROXY)
            c.setopt(pycurl.PROXYPORT, settings.OUTGOING_PROXY_PORT)
        c.setopt(pycurl.NETRC, 1)
        url = str("/%s/%s/%s" % (endpoint, self.slug, call)).replace("//", "/")
        url = self.base + url
        c.setopt(pycurl.URL, url)
        c.setopt(c.WRITEFUNCTION, self.body_callback)
        c.perform()
        c.close()

    def branches_tags(self):
        self.api_call('repositories', 'branches-tags')
        return json.loads(self.contents)

