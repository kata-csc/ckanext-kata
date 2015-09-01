Kata is a CKAN extension for handling metadata of research datasets. It is used in [Etsin research data finder](https://etsin.avointiede.fi/en/).

Installation
============

You can install the extension with:

`pip install -e git://github.com/kata-csc/ckanext-kata.git#egg=ckanext-kata`

Requirements
============

* CKAN 2.1.2
* Some additional Python packages that will be installed using `pip install`
* Extension ckanext-ytp-comments is required: https://github.com/kata-csc/ckanext-ytp-comments/tree/etsin

Configuration
=============

Put the following lines under [app:main] in CKAN configuration file

> kata.storage.malware_scan = true

> kata.is_backup = false

If Google Analytics is on, add

> kata.ga_id = [GA ID]

If LDAP is used, add basic LDAP configuration to the aforementioned file:

> kata.ldap.enabled = true

> kata.ldap.password = [LDAP PASSWORD]

> kata.ldap.server = [LDAP SERVER]

> kata.ldap.dn = [DN]

> kata.ldap.basedn = [BASE DN]
