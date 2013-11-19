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
from pylons.i18n import _
from ckanext.kata.model import KataAccessRequest
from ckan.logic import check_access, NotAuthorized
from ckanext.kata import utils

import logging

log = logging.getLogger(__name__)

TITLE_MATCH = re.compile(r'^(title_)?\d?$')


def package_show(context, data_dict):
    '''
    Called before showing the dataset in some interface (browser, API).
    '''
    pkg_dict1 = ckan.logic.action.get.package_show(context, data_dict)
    # Normally logic function should not catch the raised errors
    # but here it is needed so action package_show won't catch it instead
    # Hiding information from API calls
    try:
        check_access('package_update', context)
    except NotAuthorized:
        pkg_dict1['maintainer_email'] = _('Not authorized to see this information')
        pkg_dict1['project_funding'] = _('Not authorized to see this information')
        
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

    pkg_dict1 = utils.resource_to_dataset(pkg_dict1)

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
                     'geographic_coverage_tmp', \
                     'discipline_field_langs', 'discipline_field']
        for key in removable:
            del data_dict[key]
    except KeyError:
        pass

    data_dict = utils.dataset_to_resource(data_dict)

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

    data_dict = utils.dataset_to_resource(data_dict)

    # This is a consequence or removing the ckan_phase!
    # The solution might not be good, if further problems arise
    # a better fix will be made
    context['allow_partial_update'] = True
    pkg_dict1 = ckan.logic.action.update.package_update(context, data_dict)
    context = {'model': model, 'ignore_auth': True, 'validate': False,
               'extras_as_string': True}
    pkg_dict = ckan.logic.action.get.package_show(context, pkg_dict1)
    index = index_for('package')
    # update_dict calls index_package, so it would basically be the same
    index.update_dict(pkg_dict)
    return pkg_dict1


def package_delete(context, data_dict):
    '''
    Deletes a package
    
    Extends ckan's similar method to instantly re-index the SOLR index. 
    Otherwise the changes would only be added during a re-index (a rebuild of search index,
    to be specific).
    
    Arguments:
    :param context:
    :param data_dict: package data as dictionary
    '''
    index = index_for('package')
    index.remove_dict(data_dict)
    ret = ckan.logic.action.delete.package_delete(context, data_dict)
    return ret


def group_list(context, data_dict):
    '''
    Return a list of the names of the site's groups.
    '''
    if not "for_view" in context:
        return {}
    else:
        return ckan.logic.action.get.group_list(context, data_dict)


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
