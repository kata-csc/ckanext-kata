from ckan.lib.base import abort
from ckan.logic import NotAuthorized
from ckan.lib.base import _

class NotAuthorizedMiddleware(object):
    """ Catch and handle NotAuthorized exceptions.
    """
    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))
