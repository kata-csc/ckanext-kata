"""
The extractor module provides functions for extracting text contents from files.
"""
import subprocess
import tempfile

import urllib2
import logging
import os
import codecs

import ckan.controllers.storage as storage
import pylons.config as config
import pairtree.storage_exceptions as storage_exceptions
from ckanext.kata import settings
from ckanext.kata.utils import log

log = logging.getLogger(__name__)     # pylint: disable=invalid-name

BUCKET = config.get('ckan.storage.bucket', 'default')
STORAGE_BASE_URL = config.get('ckan.site_url') + '/storage/f/'

def extract_text(resource_url, format):
    ofs = storage.get_ofs()

    label = resource_url.split(STORAGE_BASE_URL)[-1]
    label = urllib2.unquote(label)

    format = format.lower()

    log.debug("Resource label: %s" % label)

    try:
        # Get file location
        file_path = ofs.get_url(BUCKET, label).split('file://')[-1]
    except storage_exceptions.FileNotFoundException:
        raise IOError("Unable to extract text from {u} -- is the resource remote?".format(u=resource_url))

    if format != 'txt':
        log.info("Attempting to extract plain text from {p}".format(p=file_path))
        converted_fd, converted_path = convert_file_to_text(file_path, format)
        file_path = converted_path
        if file_path is not None:
            tmp_file = True
        else:
            log.info("Extraction failed; unsupported format?")
            tmp_file = False
    else:
        tmp_file = False

    if file_path is not None:
        log.debug("Reading from %s" % file_path)
        with codecs.open(file_path, mode='r', encoding='utf-8') as text_file:
            text = text_file.read()
            log.debug("Resource plain text contents:")
            log.debug(text)
    else:
        text = u""

    if tmp_file:
        os.remove(file_path)

    return text


def convert_file_to_text(resource_file_path, format):
    """
    Returns the file descriptor and path for a temporary file that contains
    the contents of the given resource converted to plain text.

    If there is no suitable converter for the format,
    the return value will be (None, None).
    """

    prog = settings.TEXTOUTPUTPROGS[format] if (format in settings.TEXTOUTPUTPROGS and
                                                format is not 'txt') else None

    if not prog:
        return None, None
    else:
        converted_fd, converted_path = tempfile.mkstemp()

        log.debug("Converting to plain text; prog={p}, file={f}"
                  .format(p=prog['exec'], f=resource_file_path)
        )
        command = [prog['exec']]
        if prog['args']:
            command.extend(prog['args'].split())
        command.append(resource_file_path)
        if prog['output']:
            command.append(prog['output'])

        log.debug("Subprocess command: {c}".format(c=command))
        process = subprocess.Popen(command, stdout=converted_fd)
        process.communicate()
        return converted_fd, converted_path
