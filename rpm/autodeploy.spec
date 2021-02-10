%define pkgname autodeploy
%define version 1.1
%define release 2

Name: python3-%{pkgname}
Summary: An agent to listen for repo webhooks and securely deploy them
Version: %{version}
Release: %{release}
Source0: %{pkgname}-%{version}.tar.gz
License: GPLv3+
Group: Applications/System
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


%package webd
Summary: Standalone webserver component recieving git-push webhook from Gitea
Requires: python3 >= 3.5
Requires: python3-%{pkgname}
Requires: autodeploy == %{version}

%description webd
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


%pre webd
getent group adwebd >/dev/null || groupadd -r adwebd
getent passwd adwebd >/dev/null || \
useradd -r -g adwebd -d /run/autodeploy -s /sbin/nologin \
  -c "Runs Git-autodeploy standalone webserver" adwebd
exit 0

%post
systemctl daemon-reload
key=$(tr -cd '0-9a-zA-Z' < /dev/urandom  | head -c 20)
sed -i "s/^daemonkey.*=.*/daemonkey = ${key}/" /etc/autodeploy.cfg

%post webd
systemctl daemon-reload
chgrp adwebd /etc/autodeploy.cfg

%preun webd
%systemd_preun autodeploy-webd.service

%files
%doc README.md
%{_bindir}/%{pkgname}d
%{python3_sitelib}/%{pkgname}-*.egg-info/
%{python3_sitelib}/%{pkgname}/
%{_unitdir}/autodeployd.service
%attr(0640, root, -)%config(noreplace) %{_sysconfdir}/autodeploy.cfg


%files webd
%{_unitdir}/autodeploy-webd.service
%{_bindir}/%{pkgname}-webd


%changelog
* Wed Feb 10 2021 William Strecker-Kellogg <willsk@bnl.gov>
- New version, diff in email and owner option for local repo

* Fri Jan 21 2021 William Strecker-Kellogg <willsk@bnl.gov>
- Bump version, fixups for RPM pre/post scripts primarily

* Wed Dec 23 2020 William Strecker-Kellogg <willsk@bnl.gov>
- Initial specfile
