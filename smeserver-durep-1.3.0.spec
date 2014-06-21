# $Id: smeserver-durep.spec,v 1.3 2012/08/15 22:15:30 unnilennium Exp $
# Authority: unnilennnium
# Name: JP Pialasse

%define name smeserver-durep
Name:          %{name}
%define version 1.3.0
Version:       %{version}
%define release 6
Release:       %{release}%{?dist}
License:       GPL
Source:  %{name}-%{version}.tgz
Patch1: smeserver-durep-1.3.0-df.patch
BuildRoot: /var/tmp/%{name}-%{version}-buildroot
BuildRequires: e-smith-devtools
BuildArch: noarch
Group:         Networking/Daemons
Summary:       DUREP - Graphic Report for Disk Usage
Requires:      perl(Data::Dumper)
Requires:      perl(MLDBM) >= 1.21-4
Obsoletes:    smeserver-durep-saco
Obsoletes:      e-smith-durep


%changelog
* Thu Sep 13 2012 JP Pialasse <test@pialasse.com> 1.3.0-6.sme
- add Obsoletes smeserver-durep-saco e-smith-durep [SME 7108]
- TODO cleaning spec file post and filelist chmod

* Mon Sep 10 2012 JP Pialasse <test@pialasse.com> 1.3.0-5.sme
- fix do not copy files  and filelist [SME 7098]
- patch df of plugged disk 

* Sun Sep 09 2012 JP Pialasse <test@pialasse.com> 1.3.0-4.sme
- dependencies resolution

* Fri Aug 31 2012 JP Pialasse <test@pialasse.com> 1.3.0-3.sme
- build error fix : prep setup

* Wed Aug 15 2012 JP Pialasse <test@pialasse.com> 1.3.0-1.sme
- update from 1.03-02sn to comply with SME8 and SME7
- moved archives to /var/lib/durep
- moved web files to manager/html
- cleaned spec

%description
DUREP is a  Report Generator that creates graphical Output for the "du" command

%prep
%setup
%patch1 -p1

%install
/bin/rm -rf $RPM_BUILD_ROOT
(cd root;  /usr/bin/find . -depth -print | /bin/cpio -dump $RPM_BUILD_ROOT)
/bin/rm -f %{name}-%{version}-filelist
/sbin/e-smith/genfilelist $RPM_BUILD_ROOT > %{name}-%{version}-filelist


%clean
/bin/rm -rf $RPM_BUILD_ROOT

%files -f %{name}-%{version}-filelist
%defattr(-,root,root)

#%attr(0644 root root) "/etc/e-smith/templates/etc/crontab/durep"
#%attr(4750 root admin) "/etc/e-smith/web/functions/durep"
#%attr(0777 root root) "/etc/e-smith/web/panels/manager/cgi-bin/durep"
#%attr(0644 root root) "/usr/local/bin/durep"
#%dir %attr(0755 root root) "/usr/local/man"
#%dir %attr(0755 root root) "/usr/local/man/man1"
#%attr(0644 root root) "/usr/local/man/man1/durep.1"
#%dir %attr(0755 root root) "/usr/sbin"
#%attr(0644 root root) "/usr/sbin/durep.daily"
#%dir %attr(0755 root root) "/var/lib/durep"
#%dir %attr(0755 root root) "/etc/e-smith/web/panels/manager/html/durep"
#%attr(0644 root root) "/etc/e-smith/web/panels/manager/html/durep/bar.png"
#%attr(0644 root root) "/etc/e-smith/web/panels/manager/html/durep/durep.cgi"
#%attr(0644 root root) "/etc/e-smith/web/panels/manager/html/durep/style.css"

%pre -p /bin/sh

%post -p /bin/sh
chmod 755 /usr/local/bin/durep
chmod 755 /usr/sbin/durep.daily
/sbin/e-smith/expand-template /etc/crontab
echo "Initial run of durep ... please wait."
/usr/sbin/durep.daily >/dev/null
/etc/e-smith/events/actions/navigation-conf >/dev/null 2>&1

%preun -p /bin/sh

%postun -p /bin/sh
if [ "$1" = 0 ]; then
    /sbin/e-smith/expand-template /etc/crontab
    /etc/e-smith/events/actions/navigation-conf 2>/dev/null
fi

