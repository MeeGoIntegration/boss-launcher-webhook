all: install 

install:
	python setup.py -q install --root=$(DESTDIR) --prefix=$(PREFIX)
	install -D -m 644 conf/supervisor/webhook.conf    $(DESTDIR)/etc/supervisor/conf.d/webhook.conf
	install -D -m 755 src/participants/delete_webhook.py   $(DESTDIR)/usr/share/boss-skynet/delete_webhook.py
	install -D -m 755 src/participants/trigger_service.py  $(DESTDIR)/usr/share/boss-skynet/trigger_service.py
	install -D -m 644 conf/supervisor/delete_webhook.conf  $(DESTDIR)/etc/supervisor/conf.d/delete_webhook.conf
	install -D -m 644 conf/supervisor/trigger_service.conf $(DESTDIR)/etc/supervisor/conf.d/trigger_service.conf
	install -D -m 644 src/service/tar_git.service $(DESTDIR)/usr/lib/obs/service/tar_git.service
	install -D -m 755 src/service/tar_git $(DESTDIR)/usr/lib/obs/service/tar_git
	install -D -m 644 src/service/webhook.service $(DESTDIR)/usr/lib/obs/service/webhook.service
	install -D -m 755 src/service/webhook $(DESTDIR)/usr/lib/obs/service/webhook
	install -D -m 755 src/service/webhook_diff.py $(DESTDIR)/usr/lib/obs/service/webhook_diff.py

clean:
	python setup.py clean
