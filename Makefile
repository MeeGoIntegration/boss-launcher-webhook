all: install 

install:
	python setup.py install --root=$(DESTDIR) --prefix=$(PREFIX)
	install -D -m 644 conf/supervisor/webhook.conf    $(DESTDIR)/etc/supervisor/conf.d/webhook.conf

	for p in create_project delete_webhook handle_webhook relay_webhook trigger_service ; do \
	  install -D -m 755 src/participants/$$p.py  $(DESTDIR)/usr/share/boss-skynet/$$p.py ; \
	  install -D -m 644 conf/supervisor/$$p.conf $(DESTDIR)/etc/supervisor/conf.d/$$p.conf ; \
	done

	install -D -m 644 src/service/tar_git.service $(DESTDIR)/usr/lib/obs/service/tar_git.service
	install -D -m 755 src/service/tar_git $(DESTDIR)/usr/lib/obs/service/tar_git
	install -D -m 644 src/service/webhook.service $(DESTDIR)/usr/lib/obs/service/webhook.service
	install -D -m 755 src/service/webhook $(DESTDIR)/usr/lib/obs/service/webhook
	install -D -m 755 src/service/webhook_diff.py $(DESTDIR)/usr/lib/obs/service/webhook_diff.py

	install -D -m 644 src/service/webhook.service $(DESTDIR)/usr/lib/obs/service/webhook.service
	install -D -m 755 src/service/webhook $(DESTDIR)/usr/lib/obs/service/webhook
	install -D -m 755 src/service/webhook_diff.py $(DESTDIR)/usr/lib/obs/service/webhook_diff.py

clean:
	python setup.py clean
