#!/bin/bash

HERE=`dirname $0`
msgcat --use-first \
    "$HERE/../kata/i18n/fi/LC_MESSAGES/ckan.po" \
    "$HERE/../../../ckanext-shibboleth/ckanext/repoze/who/shibboleth/i18n/fi/LC_MESSAGES/ckan.po" \
    "$HERE/../../../ckanext-rems/ckanext/rems/i18n/fi/LC_MESSAGES/ckan.po" \
    "$HERE/../../../ckan/ckan/i18n/fi/LC_MESSAGES/ckan.po" \
    "$HERE/../../../ckanext-statreports/ckanext/statreports/i18n/fi/LC_MESSAGES/ckan.po" \
    "$HERE/../../../ckanext-ytp-comments/i18n/fi/LC_MESSAGES/ckanext-ytp-comments.po" \
    "$HERE/../../../ckanext-showcase/ckanext/showcase/i18n/fi/LC_MESSAGES/ckanext-showcase.po" \
    | msgfmt - -o "$HERE/../kata/i18n/fi/LC_MESSAGES/ckan.mo"

echo "Done."
