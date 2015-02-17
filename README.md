Kata is a CKAN extension for handling metadata of research datasets. It is used in Etsin research data finder at [https://etsin.avointiede.fi/en/](http://google.com).

Installation
============

You can install the extension with:

`pip install -e git://github.com/kata-csc/ckanext-kata.git#egg=ckanext-kata`

Requirements
============

* CKAN 2.1.2
* Some additional Python packages that will be installed using `pip install`

Configuration
=============

Put the following lines under [app:main] in CKAN configuration file

> kata.storage.malware_scan = true

> kata.is_backup = false
