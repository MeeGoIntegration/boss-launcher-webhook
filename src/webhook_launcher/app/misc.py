import urlparse

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

