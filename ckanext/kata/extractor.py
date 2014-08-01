"""
Functions for extracting text contents from files.
"""

import urllib2
import logging
import os

import ckan.controllers.storage as storage
import pylons.config as config
import pairtree.storage_exceptions as storage_exceptions
from ckanext.kata import utils

log = logging.getLogger(__name__)     # pylint: disable=invalid-name

BUCKET = config.get('ckan.storage.bucket', 'default')
STORAGE_BASE_URL = config.get('ckan.site_url') + '/storage/f/'

def extract_text(resource_url, format):
    log.info("*** extract_text ***")
    ofs = storage.get_ofs()

    label = resource_url.split(STORAGE_BASE_URL)[-1]
    label = urllib2.unquote(label)

    format = format.lower()

    log.info("*** Resource label: %s" % label)

    try:
        # Get file location
        file_path = ofs.get_url(BUCKET, label).split('file://')[-1]
    except storage_exceptions.FileNotFoundException:
        log.warn("Unable to extract text from {u} -- is the resource remote?".format(u=resource_url))
        raise

    if format != 'txt':
        log.info("Converting {p} to plain text".format(p=file_path))
        converted_fd, converted_path = utils.convert_file_to_text(file_path, format)
        file_path = converted_path
        tmp_file = True
    else:
        tmp_file = False

    if file_path is not None:
        log.info("*** Reading from %s" % file_path)
        with open(file_path, 'r') as text_file:
            text = text_file.read()
    else:
        text = ""

    if tmp_file:
        os.remove(file_path)

    return text

