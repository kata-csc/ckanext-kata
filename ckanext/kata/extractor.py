"""
The extractor module provides functions for extracting text contents from files.
"""

import urllib2
import logging
import os
import codecs

import ckan.controllers.storage as storage
import pylons.config as config
import pairtree.storage_exceptions as storage_exceptions
from ckanext.kata import utils

log = logging.getLogger(__name__)     # pylint: disable=invalid-name

BUCKET = config.get('ckan.storage.bucket', 'default')
STORAGE_BASE_URL = config.get('ckan.site_url') + '/storage/f/'

def extract_text(resource_url, format):
    ofs = storage.get_ofs()

    label = resource_url.split(STORAGE_BASE_URL)[-1]
    label = urllib2.unquote(label)

    format = format.lower()

    log.debug("*** Resource label: %s" % label)

    try:
        # Get file location
        file_path = ofs.get_url(BUCKET, label).split('file://')[-1]
    except storage_exceptions.FileNotFoundException:
        log.warn("Unable to extract text from {u} -- is the resource remote?".format(u=resource_url))
        raise

    if format != 'txt':
        log.debug("Extracting plain text from {p}".format(p=file_path))
        converted_fd, converted_path = utils.convert_file_to_text(file_path, format)
        file_path = converted_path
        if file_path is not None:
            tmp_file = True
        else:
            tmp_file = False
    else:
        tmp_file = False

    if file_path is not None:
        log.debug("*** Reading from %s" % file_path)
        with codecs.open(file_path, mode='r', encoding='utf-8') as text_file:
            text = text_file.read()
            log.debug("Resource plain text contents:")
            log.debug(text)
    else:
        text = u""

    if tmp_file:
        os.remove(file_path)

    return text

