"""
The extractor module provides functions for extracting text contents from resources.
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
    """
    Attempts to extract plain text contents from the CKAN resource with the
    given URL. Only local resources are supported at the moment.

    Non-plain text files are first converted to a plain text representation
    if possible.

    :param resource_url: URL string
    :param format: the file format of the resource (practically file name extension)
    :rtype: unicode
    """
    ofs = storage.get_ofs()

    label = resource_url.split(STORAGE_BASE_URL)[-1]
    label = urllib2.unquote(label)

    format = format.lower()

    log.debug("Resource label: %s" % label)

    original_path = None
    converted_path = None

    try:
        # Get file location
        original_path = ofs.get_url(BUCKET, label).split('file://')[-1]
    except storage_exceptions.FileNotFoundException:
        raise IOError("Unable to extract text from {u} -- is the resource remote?".format(u=resource_url))

    if format != 'txt':
        log.debug("Attempting to extract plain text from {p}".format(p=original_path))
        converted_fd, converted_path = convert_file_to_text(original_path, format)
        if converted_path is not None:
            tmp_file = True
        else:
            log.info("Extracting plain text from {p} failed; unsupported format?".format(p=original_path))
            tmp_file = False
    else:
        tmp_file = False
        converted_path = original_path

    if converted_path is not None:
        log.debug("Reading from %s" % converted_path)
        with codecs.open(converted_path, mode='r', encoding='utf-8') as text_file:
            text = text_file.read()
            log.debug("Resource plain text contents:")
            log.debug(text)
    else:
        text = u""

    if tmp_file:
        os.remove(converted_path)

    return text


def convert_file_to_text(resource_file_path, format):
    """
    Returns the file descriptor and path for a temporary file that contains
    the contents of the given resource converted to plain text.

    If there is no suitable converter for the format,
    the return value will be (None, None).

    :param resource_file_path: the file system path to the resource file
    :param format: the file format of the resource (
    :rtype: tuple
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
