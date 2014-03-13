# pylint: disable=no-member
'''
Kata's action overrides.
'''

import datetime
import logging

import re
from pylons import c
from pylons.i18n import _

import ckan.logic.action.get
import ckan.logic.action.create
import ckan.logic.action.update
import ckan.logic.action.delete
from ckan.model import Related, Session, Package, repo
import ckan.model as model
from ckan.lib.search import index_for, rebuild
from ckan.lib.navl.validators import ignore_missing, ignore, not_empty
from ckan.logic.validators import url_validator
from ckan.logic import check_access, NotAuthorized
from ckanext.kata import utils
import ckanext.kata.schemas as schemas


log = logging.getLogger(__name__)     # pylint: disable=invalid-name

TITLE_MATCH = re.compile(r'^(title_)?\d?$')


def package_show(context, data_dict):
    '''
    Called before showing the dataset in some interface (browser, API).
    '''
    pkg_dict1 = ckan.logic.action.get.package_show(context, data_dict)
    pkg_dict1 = utils.resource_to_dataset(pkg_dict1)

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
    user = model.User.get(context['user'])
    try:
        if data_dict['type'] == 'harvest' and not user.sysadmin:
            ckan.lib.base.abort(401, _('Unauthorized to add a harvest source'))
            
    except KeyError:
        log.debug("Tried to check the package type, but it wasn't present!")
        pass
    # Remove ONKI generated parameters for tidiness
    # They won't exist when adding via API
    try:
        removable = ['field-tags', 'tag_string_tmp', 'field-tags_langs',
                     'geographic_coverage_field_langs', 'geographic_coverage_field',
                     'geographic_coverage_tmp',
                     'discipline_field_langs', 'discipline_field']
        for key in removable:
            del data_dict[key]
    except KeyError:
        pass

    data_dict = utils.dataset_to_resource(data_dict)

    # Get version PID (or generate a new one?)
    new_version_pid = data_dict.get('new_version_pid')

    # if not new_version_pid:
    #     new_version_pid = utils.generate_pid()

    if new_version_pid:
        data_dict['pids'] = data_dict.get('pids', []) + [{'id': new_version_pid, 'type': 'version', 'provider': 'kata'}]

    pkg_dict1 = ckan.logic.action.create.package_create(context, data_dict)

    # Logging for production use
    try:
        log_str = '[' + str(datetime.datetime.now())
        log_str += ']' + ' Package created ' + 'by: ' + context['user']
        log_str += ' target: ' + pkg_dict1['id']
        log.info(log_str)
    except:
        pass

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

    :type context: dict
    :type data_dict: dict
    :param data_dict: dataset as dictionary
    '''
    # Remove ONKI generated parameters for tidiness
    # They won't exist when adding via API
    try:
        removable = ['field-tags', 'tag_string_tmp', 'field-tags_langs',
                     'geographic_coverage_field_langs', 'geographic_coverage_field',
                     'discipline_field_langs', 'discipline_field']
        for key in removable:
            del data_dict[key]
    except KeyError:
        pass

    # Get all resources here since we get only 'dataset' resources from WUI.
    temp_context = {'model': model, 'ignore_auth': True, 'validate': True,
                    'extras_as_string': True}
    temp_pkg_dict = ckan.logic.action.get.package_show(temp_context, data_dict)

    old_resources = temp_pkg_dict.get('resources', [])

    if not 'resources' in data_dict:
        # When this is reached, we are updating a dataset, not creating a new resource
        data_dict['resources'] = old_resources
        data_dict = utils.dataset_to_resource(data_dict)

    # Get all PIDs (except for package.id) from database and add new relevant PIDS there
    data_dict['pids'] = temp_pkg_dict.get('pids', [])
    data_dict['name'] = temp_pkg_dict['name']

    new_version_pid = data_dict.get('new_version_pid', None)
    if new_version_pid:
        data_dict['pids'] += [{'id': new_version_pid,
                              'type': 'version',
                              'provider': 'kata',
                              }]

    # # Check if data version has changed and if so, generate a new version_PID
    # if not data_dict['version'] == temp_pkg_dict['version']:
    #     data_dict['pids'].append(
    #         {
    #             u'provider': u'kata',
    #             u'id': utils.generate_pid(),
    #             u'type': u'version',
    #         })

    # This is a consequence of removing the ckan_phase!
    # The solution might not be good, if further problems arise
    # a better fix will be made
    context['allow_partial_update'] = True

    # This fixes extras fields being cleared when adding a resource. This is be because the extras are not properly
    # cleared in show_package_schema conversions. Some fields stay in extras and they cause all other fields to be
    # dropped in package_update(). When updating a dataset via UI or API, the conversion to extras occur in
    # package_update() and popping extras here should have no effect.

    data_dict.pop('extras', None)
    # TODO: Get rid of popping extras here and rather pop the additional extras in converters so we could remove the
    # popping and the above "context['allow_partial_update'] = True" which causes the extras to be processed in a way
    # that nothing gets added to extras from the converters and everything not initially present in extras gets removed.

    # TODO Apply correct schema depending on dataset
    # This is quick resolution. More robust way would be to check through
    # model.Package to which harvest source the dataset belongs and then get the
    # type of the harvester (eg. DDI)
    # if data_dict['name'].startswith('FSD'):
    #     context['schema'] = schemas.update_package_schema_ddi()

    pkg_dict1 = ckan.logic.action.update.package_update(context, data_dict)

    # Logging for production use
    try:
        log_str = '[' + str(datetime.datetime.now())
        log_str += ']' + ' Package updated ' + 'by: ' + context['user']
        log_str += ' target: ' + data_dict['id']
        log.info(log_str)
    except:
        pass

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
    # Logging for production use
    try:
        log_str = '[' + str(datetime.datetime.now())
        log_str += ']' + ' Package deleted ' + 'by: ' + context['user']
        log_str += ' target: ' + data_dict['id']
        log.info(log_str)
    except:
        pass

    index = index_for('package')
    index.remove_dict(data_dict)
    ret = ckan.logic.action.delete.package_delete(context, data_dict)
    return ret

# Log should show who did what and when
def _decorate(f, actiontype, action):
    def call(*args, **kwargs):
        log_str = '[ ' + actiontype + ' ] [ ' + str(datetime.datetime.now())
        if action is 'delete':
            # log id before we delete the data
            try:
                log_str += ' ] ' + actiontype + ' deleted by: ' + args[0]['user']
                log_str += ' target: ' + args[1]['id']
                log.info(log_str)
            except:
                log.info('Debug failed! Action not logged')

        ret = f(*args, **kwargs)
        if action is 'create' or action is 'update':
            try:
                log_str += ' ] ' + actiontype + ' ' + action + 'd by: ' + args[0]['user']
                log_str += ' target: ' + ret['id']
                log.info(log_str)
            except:
                log.info('Debug failed! Action not logged')

        return ret

    return call

# Overwriting to add logging
resource_create = _decorate(ckan.logic.action.create.resource_create, 'resource', 'create')
resource_update = _decorate(ckan.logic.action.update.resource_update, 'resource', 'update')
resource_delete = _decorate(ckan.logic.action.delete.resource_delete, 'resource', 'delete')
related_delete = _decorate(ckan.logic.action.delete.related_delete, 'related', 'delete')
member_create = _decorate(ckan.logic.action.create.member_create, 'member', 'create')
member_delete = _decorate(ckan.logic.action.delete.member_delete, 'member', 'delete')
group_create = _decorate(ckan.logic.action.create.group_create, 'group', 'create')
group_update = _decorate(ckan.logic.action.update.group_update, 'group', 'update')
group_delete = _decorate(ckan.logic.action.delete.group_delete, 'group', 'delete')
organization_create = _decorate(ckan.logic.action.create.organization_create, 'organization', 'create')
organization_update = _decorate(ckan.logic.action.update.organization_update, 'organization', 'update')
organization_delete = _decorate(ckan.logic.action.delete.organization_delete, 'organization', 'delete')


def package_search(context, data_dict):
    """
    Wraps around the CKAN package_search action to add customizations
    in some special cases.
    """
    if c.controller == "home" and c.action == "index":
        data_dict['sort'] = "metadata_modified desc"
        data_dict['rows'] = 5
        # don't want harvest source packages
        data_dict['q'] = "author:['' TO *]"

    return ckan.logic.action.get.package_search(context, data_dict)


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

    ret = ckan.logic.action.create.related_create(context, data_dict)
    # Logging for production use
    try:
        log_str = '[' + str(datetime.datetime.now())
        log_str += ']' + ' related created ' + 'by: ' + context['user']
        log_str += ' target: ' + ret['id']
        log.info(log_str)
    except:
        pass

    return ret


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

    # Logging for production use
    try:
        log_str = '[' + str(datetime.datetime.now())
        log_str += ']' + ' related updated ' + 'by: ' + context['user']
        log_str += ' target: ' + data_dict['id']
        log.info(log_str)
    except:
        pass

    return ckan.logic.action.update.related_update(context, data_dict)
