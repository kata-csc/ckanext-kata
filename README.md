ckanext-kata
============

KATA extensions for CKAN

Installation
============

To install this Kata-plugin

  pip install -e git://github.com/kata-csc/ckanext-kata.git#egg=ckanext-kata

.ini configuration
==================
Put following lines under [app:main]

  kata.contact_roles = Author, Maintainer, Publisher, Sponsor, Example Role
  kata.date_format = %d.%m.%Y
