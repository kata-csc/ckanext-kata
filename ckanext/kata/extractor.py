"""
Functions for extracting text contents from files.
"""

import urllib2
import logging
import tempfile

import ckan.controllers.storage as storage
import pylons.config as config
import pairtree.storage_exceptions as storage_exceptions

log = logging.getLogger(__name__)     # pylint: disable=invalid-name

BUCKET = config.get('ckan.storage.bucket', 'default')
STORAGE_BASE_URL = config.get('ckan.site_url') + '/storage/f/'

def extract_text(resource_url, format):
    log.info("*** extract_text ***")
    ofs = storage.get_ofs()

    label = resource_url.split(STORAGE_BASE_URL)[-1]
    label = urllib2.unquote(label)

    log.info("*** Resource label: %s" % label)

    try:
        # Get file location
        file_path = ofs.get_url(BUCKET, label).split('file://')[-1]
    except storage_exceptions.FileNotFoundException:
        log.warn("Unable to extract text from {u} -- is the resource remote?".format(u=resource_url))
        raise

    if format.lower() != 'txt':
        # FIXME: add conversion
        log.info("Resource not plain text and conversion is not yet supported")
        return


    log.info("*** Reading from %s" % file_path)
    with open(file_path, 'r') as text_file:
        text = text_file.read()

    return text

