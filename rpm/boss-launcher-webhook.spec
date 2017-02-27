%define svdir %{_sysconfdir}/supervisor/conf.d/
%define use_pip 1

Name: boss-launcher-webhook
Version: 0.2.0
Release: 1

Group: Applications/Engineering
License: GPLv2+
URL: http://www.merproject.org
Source: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires: python, python-setuptools, python-sphinx, python-boss-skynet, python-ruote-amqp
%if ! 0%{?use_pip}
BuildRequires: python-django
%endif
%if 0%{?fedora}
BuildRequires: MySQL-python
%else
BuildRequires: python-mysql
%endif
Requires: python >= 2.5.0, python-xml, python-boss-skynet, python-flup, python-pycurl, python-requests
%if ! 0%{?use_pip}
Requires: python-django, python-djangorestframework python-django-extensions
%endif
%if 0%{?fedora}
Requires: MySQL-python
%else
Requires: python-mysql
%endif
Requires: apache2-mod_wsgi
Requires(post): python-boss-skynet
BuildArch: noarch
Summary: VCS webhook handler

%description
Webhook handler for gitlab, github and bitbucket that receives data as a POST callback and launches a ruote process

%package -n obs-service-tar-git
Group: Applications/Engineering
Requires: git
Summary: OBS source service to generate sources from git
%description -n obs-service-tar-git
This package provides the service to generate source from git inside an OBS source service

%package -n obs-service-webhook
Group: Applications/Engineering
Requires: obs-source_service, python-lxml, python-json
Summary: OBS source service to manage webhooks
%description -n obs-service-webhook
This package provides the service to update webhooks from OBS. It ensures that only users who have access to a package can update the webhook for that package.

%package -n boss-participant-trigger_service
Group: Applications/Engineering
Requires: python-boss-skynet >= 0.6.0, boss-standard-workflow-common, python-lxml, python-buildservice >= 0.5.3
Summary: BOSS participant to handle webhooks
%description -n boss-participant-trigger_service
This package provides the participant that handles creating and/or triggering  _service files in OBS, in response to webhook triggers

%package -n boss-participant-create_project
Group: Applications/Engineering
Requires: python-boss-skynet >= 0.6.0, python-boss-common, boss-standard-workflow-common, python-lxml, boss-launcher-webhook, python-buildservice >= 0.5.3
Summary: BOSS participant to handle webhooks
%description -n boss-participant-create_project
This package provides the participant that handles creating project files in OBS, in response to webhook triggers

%define python python%{?__python_ver}
%define __python /usr/bin/%{python}
%if ! (0%{?fedora} > 12 || 0%{?rhel} > 5)
%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%{!?python_sitearch: %global python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib(1))")}
%endif

%prep
%setup -q %{name}-%{version}

%build

%install
rm -rf %{buildroot}
make PREFIX=%{_prefix} DESTDIR=%{buildroot} install

%clean
rm -rf %{buildroot}

%post
if [ $1 -ge 1 ]; then
    skynet apply || true
    skynet reload delete_webhook || true
    skynet reload handle_webhook || true
    skynet reload relay_webhook || true
fi

%post -n boss-participant-create_project
if [ $1 -ge 1 ]; then
    skynet apply || true
    skynet reload create_project || true
fi

%post -n boss-participant-trigger_service
if [ $1 -ge 1 ]; then
    skynet apply || true
    skynet reload trigger_service || true
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

%files -n boss-participant-create_project
%defattr(-,root,root,-)
%config(noreplace) %{svdir}/create_project.conf
%{_datadir}/boss-skynet/create_project.py*

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
/usr/lib/obs/service/webhook_diff.py*
