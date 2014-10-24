"""
Exceptions for use within the Kata CKAN extension.

These custom exceptions should probably be handled within the extension
rather than throwing them outside of its scope.
"""

class MailingException(Exception):
    pass
