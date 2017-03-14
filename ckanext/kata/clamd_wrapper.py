from paste.deploy.converters import asbool
from functools import wraps
from pylons import config
from ckan.logic import ValidationError
import logging
import pyclamd


log = logging.getLogger(__name__)

def _clamd_scan(stream):
    '''
    Checks for malware in the given stream using a ClamAV daemon.
    Inspired by the example code in pyclamd.

    Scanning consumes the input stream.

    :param stream: the input stream to scan
    :type stream: file-like object
    :return: True if the file is clean and False if there is a detection.
    :rtype: bool
    :raises MalwareCheckError: if connecting to the ClamAV daemon fails or there is another error
    '''

    log.debug("Running malware scan on input stream")

    try:
        daemon = pyclamd.ClamdNetworkSocket()
        daemon.ping()
    except pyclamd.ConnectionError:
        raise MalwareCheckError("Connection to ClamAV daemon failed")

    try:
        result = daemon.scan_stream(stream.read())

        if result:
            # scan_stream only returns a non-None result on error or detection
            passed = False

            status = result['stream']
            log.debug("Scan status: {s}".format(s=status))

            if status[0] == 'FOUND':
                log.warn('Malware detected in upload: {s}'.format(s=status))
            else:
                log.error('Malware scan failed: {s}'.format(s=status))
                raise MalwareCheckError(
                    "ClamAV scan produced an error: {s}".format(s=status)
                )
        else:
            passed = True
    except pyclamd.BufferTooLongError:
        raise MalwareCheckError("Uploaded file is too large for malware scan")
    except pyclamd.ConnectionError:
        raise MalwareCheckError("Connection to ClamAV daemon failed")

    return passed


def perform_scan(resource):
    '''
        Perform a malware scan and return True for a passed file
        and false for detected malware. Wraps _clamd_scan
        handling exceptions.
    '''
    do_scan = asbool(config.get('kata.storage.malware_scan', False))
    if do_scan and not isinstance(resource, unicode):
        file_buffer = resource.file
        try:
            return _clamd_scan(file_buffer)
        except clamd_wrapper.MalwareCheckError as err:
            log.error(str(err))
            return False
        finally:
            file_buffer.seek(0)  # reset the stream

    return True


def scan_for_malware(action_func):
    """
        A decorator wrapping clamd_wrapper.perform_scan, that can be used to scan 
        resource fileuploads.

        Requires a data_dict with a field 'upload' of type FieldStorage.
        i.e.    {'package_id': u'urn-nbn-fi-csc-kata12345', 
                'upload': FieldStorage('upload', u'myfile.txt'), 
                'name': u'myfile.txt'}

        Usage:
            @scan_for_malware
            def my_action_function(context, data_dict):
                return 'something'
    """
    def _decorator(request, *args, **kwargs):
        resource = args[0].get('upload')
        if not perform_scan(resource):
            raise ValidationError("Uploaded resource did not pass malware scan.")
        else:
            return action_func(request, *args, **kwargs)

    return wraps(action_func)(_decorator)


class MalwareCheckError(Exception):
    """
    Exception class that wraps/represents errors that can occur in
    clamd scans.
    """

    pass
