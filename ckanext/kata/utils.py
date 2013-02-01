from ckan.lib.email_notifications import send_notification
from pylons.i18n import gettext as _
from pylons import config
from ckan.model import User, Package
from ckan.lib import helpers as h
import logging

log = logging.getLogger(__name__)


def generate_pid():
    """ Generates dummy pid """
    import datetime
    return "urn:nbn:fi:csc-kata%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")


def send_email(req):
    requestee = User.get(req.user_id)
    pkg = Package.get(req.pkg_id)
    selrole = False
    for role in pkg.roles:
        if role.role == "admin":
            selrole = role
    if not selrole:
        return
    admin = User.get(selrole.user_id)
    msg = _("""%s (%s) is requesting editor access to a dataset you have created
    %s.

Please click this link if you want to give this user write access:
%s%s""")
    controller = 'ckanext.kata.controllers:AccessRequestController'
    body = msg % (requestee.name, requestee.email, pkg.title if pkg.title else pkg.name,
                config.get('ckan.site_url', ''),
                h.url_for(controller=controller,
                action="unlock_access",
                id=req.id))
    email_dict = {}
    email_dict["subject"] = _("Access request for dataset %s" % pkg.title if pkg.title else pkg.name)
    email_dict["body"] = body
    send_notification(admin.as_dict(), email_dict)
