%define svdir %{_sysconfdir}/supervisor/conf.d/

Name: boss-launcher-webhook
Version: 0.2.0
Release: 1

Group: Applications/Engineering
License: GPLv2+
URL: https://github.com/MeeGoIntegration/boss-launcher-webhook
Source: %{name}-%{version}.tar.gz

BuildArch: noarch

BuildRequires: python-setuptools
BuildRequires: python-rpm-macros

Requires: apache2-mod_wsgi
Requires: python-requests
Requires: python-xml
Requires: python-boss-skynet
Requires: python-Django
Requires: python-djangorestframework
Requires(post): python-boss-skynet


Summary: VCS webhook handler

%description
Webhook handler for gitlab, github and bitbucket that receives data as a POST callback and launches a ruote process

%package -n obs-service-tar-git
Requires: git, obs-source_service
Summary: OBS source service to generate sources from git
%description -n obs-service-tar-git
This package provides the service to generate source from git inside an OBS source service

%package -n obs-service-webhook
Requires: obs-source_service, python-argparse, python-requests
Summary: OBS source service to manage webhooks
%description -n obs-service-webhook
This package provides the service to update webhooks from OBS. It ensures that only users who have access to a package can update the webhook for that package.

%package -n boss-participant-trigger_service
Requires: python-boss-skynet >= 0.6.0, boss-standard-workflow-common, python-lxml, python-yaml, python-buildservice >= 0.5.3
Summary: BOSS participant to handle webhooks
%description -n boss-participant-trigger_service
This package provides the participant that handles creating and/or triggering  _service files in OBS, in response to webhook triggers

%package -n boss-participant-create_project
Requires: python-boss-skynet >= 0.6.0, python-boss-common, boss-standard-workflow-common, python-lxml, boss-launcher-webhook, python-buildservice >= 0.5.3
Summary: BOSS participant to handle webhooks
%description -n boss-participant-create_project
This package provides the participant that handles creating project files in OBS, in response to webhook triggers

%package -n boss-participant-get_src_state
Requires: python-boss-skynet >= 0.6.0, python-boss-common, boss-standard-workflow-common, python-lxml, boss-launcher-webhook, python-buildservice >= 0.5.3
Summary: BOSS participant to handle webhooks
%description -n boss-participant-get_src_state
This package provides the participant that checks that there is src is ready to build in OBS projects. Usually this means the service has succeeded.

%package -n boss-participant-auto_promote
Requires: python-boss-skynet >= 0.6.0, python-boss-common, boss-standard-workflow-common, python-lxml, boss-launcher-webhook, python-buildservice >= 0.5.3
Summary: BOSS participant to handle webhooks
%description -n boss-participant-auto_promote
This package provides the participant that handles promotion of gated projects, in response to webhook triggers


%prep
%setup -q %{name}-%{version}

%build
%python2_build

%install
%python2_install
make PREFIX=%{_prefix} DESTDIR=%{buildroot} install


%post
if [ $1 -ge 1 ]; then
    skynet apply || true
    skynet reload delete_webhook || true
    skynet reload handle_webhook || true
    skynet reload relay_webhook || true
    skynet register --all || true
fi

%post -n boss-participant-create_project
if [ $1 -ge 1 ]; then
    skynet apply || true
    skynet reload create_project || true
    skynet register --all || true
fi

%post -n boss-participant-get_src_state
if [ $1 -ge 1 ]; then
    skynet apply || true
    skynet reload get_src_state || true
    skynet register --all || true
fi

%post -n boss-participant-trigger_service
if [ $1 -ge 1 ]; then
    skynet apply || true
    skynet reload trigger_service || true
    skynet register --all || true
fi

%post -n boss-participant-auto_promote
if [ $1 -ge 1 ]; then
    skynet apply || true
    skynet reload auto_promote || true
    skynet register --all || true
fi

%files
%defattr(-,root,root,-)
%dir %{_sysconfdir}/skynet
%dir %{_sysconfdir}/apache2
%dir %{_sysconfdir}/apache2/vhosts.d
%dir %{_sysconfdir}/supervisor
%dir %{svdir}
%dir %{_datadir}/boss-skynet
%config(noreplace) %{_sysconfdir}/skynet/webhook.conf
%config(noreplace) %{_sysconfdir}/apache2/vhosts.d/webhook.conf
%config(noreplace) %{svdir}/delete_webhook.conf
%config(noreplace) %{svdir}/handle_webhook.conf
%config(noreplace) %{svdir}/relay_webhook.conf
%{python_sitelib}/webhook_launcher
%{python_sitelib}/*egg-info
%{_datadir}/webhook_launcher
%{_datadir}/boss-skynet/delete_webhook.py*
%{_datadir}/boss-skynet/handle_webhook.py*
%{_datadir}/boss-skynet/relay_webhook.py*

%files -n boss-participant-auto_promote
%defattr(-,root,root,-)
%config(noreplace) %{svdir}/auto_promote.conf
%{_datadir}/boss-skynet/auto_promote.py*

%files -n boss-participant-create_project
%defattr(-,root,root,-)
%config(noreplace) %{svdir}/create_project.conf
%{_datadir}/boss-skynet/create_project.py*

%files -n boss-participant-get_src_state
%defattr(-,root,root,-)
%config(noreplace) %{svdir}/get_src_state.conf
%{_datadir}/boss-skynet/get_src_state.py*

%files -n boss-participant-trigger_service
%defattr(-,root,root,-)
%config(noreplace) %{svdir}/trigger_service.conf
%{_datadir}/boss-skynet/trigger_service.py*

%files -n obs-service-tar-git
%defattr(-,root,root,-)
%dir /usr/lib/obs
%dir /usr/lib/obs/service
/usr/lib/obs/service/tar_git
/usr/lib/obs/service/tar_git.service

%files -n obs-service-webhook
%defattr(-,root,root,-)
%dir /usr/lib/obs
%dir /usr/lib/obs/service
/usr/lib/obs/service/webhook
/usr/lib/obs/service/webhook.service
