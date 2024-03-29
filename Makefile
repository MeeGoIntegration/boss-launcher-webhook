all: install 

install:
	for p in $$(cd src/participants; ls *py | cut -f1 -d.) ; do \
	  install -D -m 755 src/participants/$$p.py  $(DESTDIR)/usr/share/boss-skynet/$$p.py ; \
	  install -D -m 644 conf/supervisor/$$p.conf $(DESTDIR)/etc/supervisor/conf.d/$$p.conf ; \
	done

	install -D -m 644 src/service/webhook.service $(DESTDIR)/usr/lib/obs/service/webhook.service
	install -D -m 755 src/service/webhook $(DESTDIR)/usr/lib/obs/service/webhook
