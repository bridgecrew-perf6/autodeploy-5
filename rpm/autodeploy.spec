%define pkgname autodeploy
%define version 0.5.0
%define release 1

Name: python3-%{pkgname}
Summary: An agent to listen for repo webhooks and securely deploy them
Version: %{version}
Release: %{release}
Source0: %{pkgname}-%{version}.tar.gz
License: INTERNAL
Group: Development/Libraries
BuildArch: noarch
Vendor: William Strecker-Kellogg <willsk@bnl.gov>
Provides: autodeploy
Url: https://git.racf.bnl.gov/gitea/willsk/autodeploy-gitea

Requires: python3 >= 3.5

BuildRequires: python3-setuptools
BuildRequires: python3-devel

Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd

%description
Service to sync from a gitea webhook to a server as securely as possible

There are two components to this, one receiver that takes the output of the
webhook POST-ed by Gitea and checks the signature and validity of the branch
and repository against the repo and key in a config file, and another that
acts on the local filesystem by checking out the changes from the pushed webhook
into a cloned repo.


%package webserver
Summary: Standalone webserver component recieving git-push webhook from Gitea
Requires: python3 >= 3.5
Requires: python3-%{pkgname}
Requires: autodeploy == %{version}

%description webserver
A standalone webserver that that listens for Gitea webhook POST events as an
alternative to the CGI script in the example directory of the autodeploy package

%prep
%autosetup -n %{pkgname}-%{version}

%build
%py3_build

%install
%py3_install
mkdir -p %{buildroot}%{_unitdir}
mkdir -p %{buildroot}%{_sysconfdir}

# Systemd units
mv %{buildroot}%{python3_sitelib}/%{pkgname}/systemd/* \
    %{buildroot}%{_unitdir}
rmdir %{buildroot}%{python3_sitelib}/%{pkgname}/systemd/

# Skeleton config file
mv %{buildroot}%{python3_sitelib}/%{pkgname}/conf.sample \
    %{buildroot}%{_sysconfdir}/autodeploy.cfg


%pre webserver
getent group autodeploywebd >/dev/null || groupadd -r autodeploywebd
getent passwd autodeploywebd >/dev/null || \
useradd -r -g autodeploywebd -d /run/autodeploy -s /sbin/nologin \
  -c "Runs Git-autodeploy standalone webserver" autodeploywebd
exit 0

%post
systemctl daemon-reload

%post webserver
systemctl daemon-reload

%preun webserver
%systemd_preun autodeploy-webserver.service

%files
%doc README.md
%{_bindir}/%{pkgname}d
%{python3_sitelib}/%{pkgname}-*.egg-info/
%{python3_sitelib}/%{pkgname}/
%{_unitdir}/autodeployd.service
%config(noreplace) %{_sysconfdir}/autodeploy.cfg


%files webserver
%{_unitdir}/autodeploy-webserver.service
%{_bindir}/%{pkgname}-webd


%changelog
* Wed Dec 23 2020 William Strecker-Kellogg <willsk@bnl.gov>
- Initial specfile
