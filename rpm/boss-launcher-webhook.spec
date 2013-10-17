%define svdir %{_sysconfdir}/supervisor/conf.d/

Name: boss-launcher-webhook
Version: 0.1.0
Release: 1

Group: Applications/Engineering
License: GPLv2+
URL: http://www.meego.com
Source: %{name}-%{version}.tar.gz
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildRequires: python, python-distribute, python-sphinx, python-boss-skynet, python-ruote-amqp, python-django
%if 0%{?fedora}
BuildRequires: MySQL-python
%else
BuildRequires: python-mysql
%endif
Requires: python-django, python-flup
%if 0%{?fedora}
Requires: MySQL-python
%else
Requires: python-mysql
%endif
Requires: python >= 2.5.0
Requires: python-xml
Requires: python-boss-skynet
Requires: python-django-south
Requires: python-django-extensions
Requires(post): python-boss-skynet
BuildArch: noarch
Summary: VCS webhook handler

%description
Webhook handler for github and bitbucket that receives data as a POST callback and launches a ruote process

%package -n obs-service-tar-git
Group: Applications/Engineering
Requires: git, obs-source_service
Summary: OBS source service to generate sources from git
%description -n obs-service-tar-git
This package provides the service to generate source from git inside an OBS source service

%package -n boss-participant-trigger_service
Group: Applications/Engineering
Requires: python-boss-skynet >= 0.6.0, boss-standard-workflow-common
Summary: BOSS participant to handle webhooks
%description -n boss-participant-trigger_service
This package provides the participant that handles creating _service files in OBS, in response to webhook triggers

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
if [ "$1" == 0 ]; then
  skynet reload webhook delete_webhook
fi

%post -n boss-participant-trigger_service
if [ "$1" == 0 ]; then
  skynet reload trigger_service
fi

%files
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/skynet/webhook.conf
%{python_sitelib}/webhook_launcher
%{python_sitelib}/*egg-info
%{_datadir}/webhook_launcher
%config(noreplace) %{svdir}/webhook.conf
%config(noreplace) %{svdir}/delete_webhook.conf
%dir /etc/skynet
%dir /etc/supervisor
%dir /etc/supervisor/conf.d
%dir /usr/share/boss-skynet
%{_datadir}/boss-skynet/delete_webhook.py*

%files -n boss-participant-trigger_service
%defattr(-,root,root,-)
%config(noreplace) %{svdir}/trigger_service.conf
%{_datadir}/boss-skynet/trigger_service.py*

%files -n obs-service-tar-git
%defattr(-,root,root,-)
/usr/lib/obs/service
/usr/lib/obs
