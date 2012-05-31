%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           cloud-init
Version:        0.6.3
Release:        0.4.bzr532%{?dist}
Summary:        Cloud instance init scripts

Group:          System Environment/Base
License:        GPLv3
URL:            http://launchpad.net/cloud-init
# bzr export -r 532 cloud-init-0.6.3-bzr532.tar.gz lp:cloud-init
Source0:        %{name}-%{version}-bzr532.tar.gz
Source1:        cloud-init-fedora.cfg
Source2:        cloud-init-README.fedora
Source3:        cloud-config.init
Source4:        cloud-final.init
Source5:        cloud-init.init
Source6:        cloud-init-local.init
Source7:        cc_yum_packages.py

Patch0:         cloud-init-0.6.3-fedora.patch
# Make runparts() work on Fedora
# https://bugs.launchpad.net/cloud-init/+bug/934404
Patch1:         cloud-init-0.6.3-no-runparts.patch
# https://bugs.launchpad.net/cloud-init/+bug/970071
Patch2:         cloud-init-0.6.3-lp970071.patch
# Support subprocess.check_output on python < 2.7
Patch3:         cloud-init-check_output.patch
# Support subprocess.CalledProcessError on python < 2.7
Patch4:         cloud-init-calledprocesserror.patch

BuildArch:      noarch
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-devel
BuildRequires:  python-setuptools-devel
Requires:       e2fsprogs
Requires:       iproute
Requires:       libselinux-python
Requires:       net-tools
Requires:       procps
Requires:       python-boto
Requires:       python-cheetah
Requires:       python-configobj
Requires:       PyYAML
Requires:       rsyslog
Requires:       shadow-utils
Requires:       /usr/bin/run-parts
Requires(post):   chkconfig
Requires(preun):  chkconfig
Requires(postun): initscripts

%description
Cloud-init is a set of init scripts for cloud instances.  Cloud instances
need special scripts to run during initialization to retrieve and install
ssh keys and to let the user run various scripts.


%prep
%setup -q -n %{name}-%{version}-bzr532
%patch0 -p0
%patch1 -p0
%patch2 -p1
%patch3 -p1
%patch4 -p0

cp -p %{SOURCE2} README.fedora


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

for x in $RPM_BUILD_ROOT/%{_bindir}/*.py; do mv "$x" "${x%.py}"; done
chmod +x $RPM_BUILD_ROOT/%{python_sitelib}/cloudinit/SshUtil.py
mkdir -p $RPM_BUILD_ROOT/%{_sharedstatedir}/cloud

# We supply our own config file since our software differs from Ubuntu's.
cp -p %{SOURCE1} $RPM_BUILD_ROOT/%{_sysconfdir}/cloud/cloud.cfg
cp -p %{SOURCE7} $RPM_BUILD_ROOT/%{python_sitelib}/cloudinit/CloudConfig/cc_yum_packages.py

# Note that /etc/rsyslog.d didn't exist by default until F15.
# el6 request: https://bugzilla.redhat.com/show_bug.cgi?id=740420
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d
cp -p tools/21-cloudinit.conf $RPM_BUILD_ROOT/%{_sysconfdir}/rsyslog.d/21-cloudinit.conf

# Install the init scripts
install -p -D -m 755 %{SOURCE3} %{buildroot}%{_initrddir}/cloud-config
install -p -D -m 755 %{SOURCE4} %{buildroot}%{_initrddir}/cloud-final
install -p -D -m 755 %{SOURCE5} %{buildroot}%{_initrddir}/cloud-init
install -p -D -m 755 %{SOURCE6} %{buildroot}%{_initrddir}/cloud-init-local


%clean
rm -rf $RPM_BUILD_ROOT


%post
if [ $1 -eq 1 ] ; then
    # Initial installation
    # Enabled by default per "runs once then goes away" exception
    for svc in config final init init-local; do
        chkconfig --add cloud-$svc
        chkconfig cloud-$svc on
    done
fi

%preun
if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    for svc in config final init init-local; do
        chkconfig --del cloud-$svc
        chkconfig cloud-$svc on
    done
    # One-shot services -> no need to stop
fi

%postun
# One-shot services -> no need to restart


%files
%doc ChangeLog LICENSE TODO README.fedora
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg
%dir               %{_sysconfdir}/cloud/cloud.cfg.d
%config(noreplace) %{_sysconfdir}/cloud/cloud.cfg.d/*.cfg
%doc               %{_sysconfdir}/cloud/cloud.cfg.d/README
%dir               %{_sysconfdir}/cloud/templates
%config(noreplace) %{_sysconfdir}/cloud/templates/*
%{_initrddir}/cloud-*
%{python_sitelib}/*
%{_libexecdir}/%{name}
%{_bindir}/cloud-init*
%doc %{_datadir}/doc/%{name}
%dir %{_sharedstatedir}/cloud

%config(noreplace) %{_sysconfdir}/rsyslog.d/21-cloudinit.conf


%changelog
* Thu May 31 2012 Francisco Souza <f@souza.cc> - 0.6.4-0.4.bzr532
- Support CentOS 6.2
- Added yum-packages module

* Tue May 22 2012 Pádraig Brady <P@draigBrady.com> - 0.6.3-0.4.bzr532
- Support EPEL 6

* Sat Mar 31 2012 Andy Grimm <agrimm@gmail.com> - 0.6.3-0.2.bzr532
- Fixed incorrect interpretation of relative path for
  AuthorizedKeysFile (BZ #735521)

* Mon Mar  5 2012 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.3-0.1.bzr532
- Rebased against upstream rev 532
- Fixed runparts() incompatibility with Fedora

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.6.2-0.8.bzr457
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Wed Oct  5 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.7.bzr457
- Disabled SSH key-deleting on startup

* Wed Sep 28 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.6.bzr457
- Consolidated selinux file context patches
- Fixed cloud-init.service dependencies
- Updated sshkeytypes patch
- Dealt with differences from Ubuntu's sshd

* Sat Sep 24 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.5.bzr457
- Rebased against upstream rev 457
- Added missing dependencies

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.4.bzr450
- Added more macros to the spec file

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.3.bzr450
- Fixed logfile permission checking
- Fixed SSH key generation
- Fixed a bad method call in FQDN-guessing [LP:857891]
- Updated localefile patch
- Disabled the grub_dpkg module
- Fixed failures due to empty script dirs [LP:857926]

* Fri Sep 23 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.2.bzr450
- Updated tzsysconfig patch

* Wed Sep 21 2011 Garrett Holmstrom <gholms@fedoraproject.org> - 0.6.2-0.1.bzr450
- Initial packaging
