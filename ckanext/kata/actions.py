import re
import json
import datetime
import ckan.logic.action.get
import ckan.logic.action.create
import ckan.logic.action.update
from pylons import c, config
from ckan.logic.action.create import related_create
from ckan.model import Related, Session, Package, repo
from ckan.model.authz import add_user_to_role
import ckan.model as model
from ckan.lib.search import index_for
from ckan.lib.navl.validators import ignore_missing, ignore, not_empty
from ckan.logic.validators import url_validator
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
    return pkg_dict1


def package_create(context, data_dict):
    pkg_dict1 = ckan.logic.action.create.package_create(context, data_dict)
    context = {'model': model, 'ignore_auth': True, 'validate': False,
               'extras_as_string': False}
    pkg_dict = ckan.logic.action.get.package_show(context, pkg_dict1)
    index = index_for('package')
    index.index_package(pkg_dict)
    return pkg_dict1


def group_list(context, data_dict):
    if not "for_view" in context:
        return {}
    else:
        return ckan.logic.action.get.group_list(context, data_dict)


def accessreq_show(context, data_dict):
    ret = {}
    ret['title'] = _('Request edit rights')
    smtp = config.get('smtp.server', '')
    if not len(smtp):
        ret['ret'] = 'Yes'
        return ret
    pkg = Package.get(data_dict['id'])
    selrole = False
    ret['id'] = pkg.id
    for role in pkg.roles:
        if role.role == "admin":
            selrole = True
    ret['no_owner'] = not selrole
    if c.userobj:
        if 'id' in data_dict:
            req = KataAccessRequest.is_requesting(c.userobj.id, data_dict['id'])
            if req:
                ret['ret'] = 'Yes'
                return ret
            else:
                ret['ret'] = 'No'
                return ret
        else:
            ret['ret'] = 'No'
            return ret
    ret['ret'] = 'No'
    return ret


def related_create(context, data_dict):
    schema = {
        'id': [ignore_missing, unicode],
        'title': [not_empty, unicode],
        'description': [ignore_missing, unicode],
        'type': [not_empty, unicode],
        'image_url': [ignore_missing, unicode, url_validator],
        'url': [ignore_missing, unicode],
        'owner_id': [not_empty, unicode],
        'created': [ignore],
        'featured': [ignore_missing, int],
    }
    context['schema'] = schema

    return ckan.logic.action.create.related_create(context, data_dict)


def related_update(context, data_dict):
    schema = {
        'id': [ignore_missing, unicode],
        'title': [not_empty, unicode],
        'description': [ignore_missing, unicode],
        'type': [not_empty, unicode],
        'image_url': [ignore_missing, unicode, url_validator],
        'url': [ignore_missing, unicode],
        'owner_id': [not_empty, unicode],
        'created': [ignore],
        'featured': [ignore_missing, int],
    }
    context['schema'] = schema

    return ckan.logic.action.update.related_update(context, data_dict)
