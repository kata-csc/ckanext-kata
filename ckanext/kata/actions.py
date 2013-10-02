import re

import ckan.logic.action.get
import ckan.logic.action.create
import ckan.logic.action.update
from pylons import c, config
from ckan.model import Related, Session, Package, repo
import ckan.model as model
from ckan.lib.search import index_for, rebuild
from ckan.lib.navl.validators import ignore_missing, ignore, not_empty
from ckan.logic.validators import url_validator
from pylons.i18n import gettext as _
from ckanext.kata.model import KataAccessRequest

import logging
log = logging.getLogger(__name__)

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

    # Update package.title to match package.extras.title_0

    extras_title = pkg.extras.get(u'title_0')
    if extras_title and extras_title != pkg.title:
        repo.new_revision()
        pkg.title = pkg.extras[u'title_0']
        pkg.save()
        rebuild(pkg.id)  # Rebuild solr-index for this dataset

    return pkg_dict1


def package_create(context, data_dict):
    """
    Creates a new dataset.
    
    Extends ckan's similar method to instantly reindex the SOLR index, 
    so that this newly added package emerges in search results instantly instead of 
    during the next timed reindexing.
    
    Arguments: 
    :param context    - ?
    :param data_dict  - ?
    """
    # Remove ONKI generated parameters for tidiness
    # They won't exist when adding via API
    try:
        removable = ['field-tags', 'tag_string_tmp', 'field-tags_langs', \
                     'geographic_coverage_field_langs', 'geographic_coverage_field', \
                     'discipline_field_langs', 'discipline_field']
        for key in removable:
            del data_dict[key]
    except KeyError:
        pass
    pkg_dict1 = ckan.logic.action.create.package_create(context, data_dict)
    context = {'model': model, 'ignore_auth': True, 'validate': False,
               'extras_as_string': False}
    pkg_dict = ckan.logic.action.get.package_show(context, pkg_dict1)
    index = index_for('package')
    index.index_package(pkg_dict)
    return pkg_dict1

def package_update(context, data_dict):
    '''
    Updates the dataset.
    
    Extends ckan's similar method to instantly re-index the SOLR index. 
    Otherwise the changes would only be added during a re-index (a rebuild of search index,
    to be specific).
    
    Arguments:
    :param context:
    :param data_dict: package data as dictionary
    '''
    # Remove ONKI generated parameters for tidiness
    # They won't exist when adding via API
    try:
        removable = ['field-tags', 'tag_string_tmp', 'field-tags_langs', \
                     'geographic_coverage_field_langs', 'geographic_coverage_field', \
                     'discipline_field_langs', 'discipline_field']
        for key in removable:
            del data_dict[key]
    except KeyError:
        pass
    pkg_dict1 = ckan.logic.action.update.package_update(context, data_dict)
    context = {'model': model, 'ignore_auth': True, 'validate': False,
               'extras_as_string': True}
    pkg_dict = ckan.logic.action.get.package_show(context, pkg_dict1)
    index = index_for('package')
    # update_dict calls index_package, so it would basically be the same
    index.update_dict(pkg_dict)
    return pkg_dict1

def group_list(context, data_dict):
    if not "for_view" in context:
        return {}
    else:
        return ckan.logic.action.get.group_list(context, data_dict)


def accessreq_show(context, data_dict):
    """
    Handles the requests of edit rights to the dataset. 
    
    From the web page you can find this when viewing a dataset not owned by you. In the upper right corner you can 
    request edit rights to this package from a button. The owner will receive a url via e-mail (sent daily) and by 
    clicking the url (s)he can provide edit rights to the requesting person. 
    """
    
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
