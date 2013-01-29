import re
import json
import datetime
import ckan.logic.action.get
from pylons import c
from ckan.logic.action.create import related_create
from ckan.model import Related, Session, Package, repo
from ckan.model.authz import add_user_to_role
import ckan.model as model
from ckan.lib.search import index_for
from pylons.i18n import gettext as _
from model import KataAccessRequest
from sqlalchemy import exceptions
import utils

TITLE_MATCH = re.compile(r'^(title_)?\d?$')


def package_show(context, data_dict):
    pkg_dict1 = ckan.logic.action.get.package_show(context, data_dict)
    pkg = Package.get(pkg_dict1['id'])
    if 'erelated' in pkg.extras:
        erelated = pkg.extras['erelated']
        if len(erelated):
            for value in erelated.split(';'):
                if len(Session.query(Related).filter(Related.title == value).all()) == 0:
                    data_dict = {'title': value,
                                 'type': _("Paper"),
                                 'dataset_id': pkg.id}
                    related_create(context, data_dict)
    if not pkg.title:
        for key in pkg.extras.keys():
            if TITLE_MATCH.match(key):
                repo.new_revision()
                pkg.title = pkg.extras[key]
                pkg.save()
                break
    context = {'model': model, 'ignore_auth': True, 'validate': False,
               'extras_as_string': False}
    pkg_dict = ckan.logic.action.get.package_show(context, data_dict)
    index = index_for('package')
    index.index_package(pkg_dict)
    return pkg_dict1


def group_list(context, data_dict):
    if not "for_view" in context:
        return {}
    else:
        return ckan.logic.action.get.group_list(context, data_dict)


def reqaccess(context, data_dict):
    if c.userobj:
        if 'id' in data_dict:
            req = KataAccessRequest.is_requesting(c.userobj.id, data_dict['id'])
            if req:
                return {'ret': 'Yes'}
            else:
                # Do your emailing here
                requ = KataAccessRequest(c.userobj.id, data_dict['id'])
                requ.save()
                utils.send_email(requ)
                return {'ret': 'Yes'}
        else:
            return {'ret': 'No'}
    return {'ret': 'No'}
