Name: mikes-wiki
Version: 1.0
Release: 1
Summary: Mike's Notebook Wiki (MkDocs site + optional Flask forum)
License: Proprietary
Source0: mikes-wiki-1.0.tar.gz
BuildArch: noarch

%description
A self-contained wiki site generated from content in ~/dev. Includes a static MkDocs site and an optional Flask forum service.

%prep
%setup -q

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/mikes-wiki
cp -r * %{buildroot}/opt/mikes-wiki/

%files
/opt/mikes-wiki

%post
if [ -d /opt/mikes-wiki/forum ]; then
  python3 -m venv /opt/mikes-wiki/venv || true
  /opt/mikes-wiki/venv/bin/python -m pip install --no-index --find-links /opt/mikes-wiki/vendor -r /opt/mikes-wiki/forum/requirements.txt || true
fi

%changelog
* Thu Apr 16 2026 Mike - 1.0-1
- initial package
