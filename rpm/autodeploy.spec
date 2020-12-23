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

BuildRequires: python3-setuptools
BuildRequires: python3-devel
BuildRequires: python3dist(setuptools)

%description
# Gitdeploy
Service to sync from a gitea webhook to a server as securely as possible

There are two components to this, one receiver that takes the output of the
webhook POST-ed by Gitea and checks the signature and validity of the branch
and repository against the repo and key in a config file, and another that
acts on the local filesystem by checking out the changes from the pushed webhook into a cloned repo.


%prep
%autosetup -n %{pkgname}-%{version}

%build
%py3_build

%install
%py3_install
mkdir -p %{buildroot}%{_prefix}/lib/systemd/system
mv %{buildroot}%{python3_sitelib}/%{pkgname}/systemd/* %{buildroot}%{_prefix}/lib/systemd/system/
rmdir %{buildroot}%{python3_sitelib}/%{pkgname}/systemd/
mv %{buildroot}%{python3_sitelib}/%{pkgname}/conf.sample %{buildroot}%{_sysconfdir}/autodeploy.cfg

%files
# %license LICENSE.rst
# %doc CHANGES.rst README.rst
%{_bindir}/%{pkgname}d
%{_bindir}/%{pkgname}-webd
%{python3_sitelib}/%{pkgname}-*.egg-info/
%{python3_sitelib}/%{pkgname}/


%changelog
* Wed Dec 23 2020 William Strecker-Kellogg <willsk@bnl.gov>
- Initial specfile
