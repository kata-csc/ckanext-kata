import logging
import pyclamd

log = logging.getLogger(__name__)

def scan_for_malware(stream):
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


class MalwareCheckError(Exception):
    """
    Exception class that wraps/represents errors that can occur in
    clamd scans.
    """

    pass
