# coding=utf8
"""
Functions to convert dataset form fields from or to db fields.
"""
import json
from iso639 import languages

from ckan.lib import helpers as h

import re
import logging
from pylons.i18n import _
from ckan.lib.navl.dictization_functions import missing

from ckan.logic.action.create import related_create
from ckan.model import Related, Session, Group, repo
from ckan.model.authz import setup_default_user_roles

from ckanext.kata import settings, utils

log = logging.getLogger('ckanext.kata.converters')


def org_auth_to_extras(key, data, errors, context):
    '''
    Convert author and organization to extras
    '''
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    if len(data[key]) > 0:
        if key[0] == 'orgauth':
            if (not ('orgauth', key[1], 'org') in data or
                    len(data[('orgauth', key[1], 'org')]) == 0):
                errors[key].append(_('Organisation is missing'))
            if (not ('orgauth', key[1], 'value') in data or
                    len(data[('orgauth', key[1], 'value')]) == 0):
                errors[key].append(_('Author is missing'))

        oval = data[(key[0], key[1], 'org')]

        extras.append({'key': "author_%s" % key[1],
                      'value': data[key]})
        extras.append({'key': 'organization_%s' % key[1],
                       'value': oval
                       })


def org_auth_from_extras(key, data, errors, context):
    '''
    Convert (author, organization) pairs from `package.extra` to `orgauths` dict

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    orgauths = data.get(('orgauth',), [])
    if not orgauths:
        data[('orgauth',)] = orgauths
    authors = []
    orgs = []
    for k in data.keys():
        if 'extras' in k and 'key' in k:
            if re.search('^(author_)\d+$', data[k]):
                val = data[(k[0], k[1], 'value')]
                author = {'key': data[k], 'value': val}
                if author not in authors:
                    authors.append(author)
                data.pop((k[0], k[1], 'value'), None)
                data.pop((k[0], k[1], '__extras'), None)
                data.pop(k, None)
                continue

            if re.search('^(organization_)\d+$', data[k]):
                val = data[(k[0], k[1], 'value')]
                org = {'key': data[k], 'org': val}
                if org not in orgs:
                    orgs.append(org)
                data.pop((k[0], k[1], 'value'), None)
                data.pop((k[0], k[1], '__extras'), None)
                data.pop(k, None)

    orgs = sorted(orgs, key=lambda ke: int(ke['key'].rsplit('_', 1)[1]))
    authors = sorted(authors, key=lambda ke: int(ke['key'].rsplit('_', 1)[1]))
    for org, author in zip(orgs, authors):
        orgauth = {}
        orgauth.update({'value': author['value']})
        orgauth.update({'org': org['org']})
        if not orgauth in orgauths:
            orgauths.append(orgauth)

def gen_translation_str_from_langtitle(key, data, errors, context):
    '''
    Fetch all the langtitle fields of type
    ('langtitle', n, 'lang'): u'en',
    ('langtitle', n, 'value'): u'translation'

    and generate a JSON translation string of type
    title: {'en':'translation', 'fi':'kaannos'}

    This converter is called only once for the hidden field
    'title' where the data is then stored.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''

    # For API requests, we need to validate if the
    # title data is already given in the new format, and
    # no langtitles given. In that case, do nothing.
    if data.get(('title',)) and not data.get(('langtitle', 0, 'lang')):
        json_string = data.get(('title',))

        json_data = {}
        try:
            json_data = json.loads(json_string)
        except ValueError:
            errors[key].append(_('The given title string is not JSON parseable'))

        # we also need to validate the keys:
        for k in json_data.keys():
            try:
                languages.get(part3=k)
            except KeyError:
                errors[key].append(_('The language code is not in ISO639-3 format'))

        return

    json_data = {}

    # loop through all the title translations
    i = 0
    while data.get(('langtitle', i, 'lang'), []):
        lval = data[('langtitle', i, 'lang')]
        rval = data[('langtitle', i, 'value')]
        if rval:    # skip a language without translation
            json_data[lval] = rval
        i+=1

    data[('title',)] = json.dumps(json_data)

def gen_translation_str_from_extras(key, data, errors, context):
    '''
    This converter is only used for converting the
    old format title fields from extras to the new JSON format
    in order to retain the compatibility between the new and
    the old format.

    1)  Check that the title isn't already in new format
    2)  If it's not, fetch the title translations from extras
    3)  convert the data to the new JSON format
    4)  dump the jason string to the data dict's
        title field.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''

    # NOTE: the title isn't updated to the database in this case,
    # should the whole conversion logic be done in actions.py instead?

    # check that title isn't already of new JSON format
    # otherwise, parse the JSON title from extras
    json_string = data.get(('title',))
    try:
        json.loads(json_string)
    except ValueError:
        if not data.get(('langtitle',)):
            # use the existing converter to fetch the data from the extras
            # and create a langtitle field.
            ltitle_from_extras(key, data, errors, context)
            langtitles = data.get(('langtitle',))

            # convert the extras to the new JSON format here
            json_data = {}
            for langtitle in langtitles:
                json_data[langtitle['lang']] = langtitle['value']

            data[('title',)] = json.dumps(json_data)



def ltitle_to_extras(key, data, errors, context):
    '''
    Convert title & language pair from dataset form to db format and validate.
    Title & language pairs will be stored in package_extra.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras

    if len(data[key]) > 0:
        # Get title's language from data dictionary. key[0] == 'title'.
        lval = data[(key[0], key[1], 'lang')]

        extras.append({'key': "title_%s" % key[1],
                      'value': data[key]})
        extras.append({'key': 'lang_title_%s' % key[1],
                       'value': lval
                       })


def ltitle_from_extras(key, data, errors, context):
    '''
    Convert all title & language pairs from db format to dataset form format.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    langtitles = data.get(('langtitle',), [])
    if not langtitles:
        data[('langtitle',)] = langtitles
    titles = []
    langs = []
    for k in data.keys():
        if 'extras' in k and 'key' in k:
            if re.search('^(title_|ltitle)\d+$', data[k]):
                val = data[(k[0], k[1], 'value')]
                title = {'key': data[k], 'value': val}
                if title not in titles:
                    titles.append(title)
                data.pop((k[0], k[1], 'value'), None)
                data.pop((k[0], k[1], '__extras'), None)
                data.pop(k, None)
                continue

            if re.search('^(lsel|lang_title_)\d+$', data[k]):
                val = data[(k[0], k[1], 'value')]
                lang = {'key': data[k], 'lang': val}
                if lang not in langs:
                    langs.append(lang)
                data.pop((k[0], k[1], 'value'), None)
                data.pop((k[0], k[1], '__extras'), None)
                data.pop(k, None)
                
    langs = sorted(langs, key=lambda ke: int(ke['key'].rsplit('_', 1)[1]))
    titles = sorted(titles, key=lambda ke: int(ke['key'].rsplit('_', 1)[1]))
    for lang, title in zip(langs, titles):
        langtitle = {}
        langtitle.update({'value': title['value']})
        langtitle.update({'lang': lang['lang']})
        if not langtitle in langtitles:
            langtitles.append(langtitle)


def export_as_related(key, data, errors, context):
    '''
    Not used?
    '''
    # Todo: find out if this is used
    if 'id' in data[('__extras',)]:
        for value in data[key].split(';'):
            if value != '':
                if len(Session.query(Related).filter(Related.title == value).all()) == 0:
                    data_dict = {'title': value,
                                 'type': _("Paper"),
                                 'dataset_id': data[('__extras',)]['id']}
                    related_create(context, data_dict)


def add_to_group(key, data, errors, context):
    '''
    Add a new group if it doesn't yet exist.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    val = data.get(key)
    if val:
        repo.new_revision()
        grp = Group.get(val)
        # UI code needs group created if it does not match. Hence do so.
        if not grp:
            grp = Group(name=val, description=val, title=val)
            setup_default_user_roles(grp)
            grp.save()
        repo.commit()


def remove_disabled_languages(key, data, errors, context):
    '''
    If `langdis == 'True'`, remove all languages.

    Expecting language codes in `data['key']`.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    langdis = data.get(('langdis',))

    langs = data.get(key).split(',')

    if langdis == 'False':
        # Language enabled

        if langs == [u'']:
            errors[key].append(_('No language given'))
    else:
        # Language disabled

        # Display flash message if user is loading a page.
        if 'session' in globals():
            h.flash_notice(_("Language is disabled, removing languages: '%s'" % data[key]))

        # Remove languages.
        del data[key]
        data[key] = u''


def remove_access_application_new_form(key, data, errors, context):
    '''
    If availability changes remove access_application_new_form.

    Expecting string: `True` or `False` in `data['key']`.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    if data.get(('availability',)) != 'access_application':
        # Remove checkbox value.
        del data[key]
        data[key] = u''


def checkbox_to_boolean(key, data, errors, context):
    '''
    Convert HTML checkbox's value ('on' / null) to boolean string
    '''
    value = data.get(key, None)

    if value not in [u'True', u'False']:
        if value == u'on':
            data[key] = u'True'
        else:
            data[key] = u'False'


def update_pid(key, data, errors, context):
    '''
    Replace an empty unicode string with random PID.
    '''
    if type(data[key]) == unicode:
        if len(data[key]) == 0:
            data[key] = utils.generate_pid()


def convert_from_extras_kata(key, data, errors, context):
    '''
    Convert all extras fields from extras to data dict and remove
    fields from extras. Removal helps counter IndexError with unflatten after
    validation.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key' and data[k] in settings.KATA_FIELDS:
            key = ''.join(data[k])
            data[(key,)] = data[(k[0], k[1], 'value')]
            for _remove in data.keys():
                if _remove[0] == 'extras' and _remove[1] == k[1]:
                    del data[_remove]


def convert_to_extras_kata(key, data, errors, context):
    '''
    Convert one extras fields from extras to data dict and remove
    fields from extras. Removal helps counter IndexError with unflatten after
    validation.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    extras.append({'key': key[-1], 'value': data[key]})


def xpath_to_extras(key, data, errors, context):
    '''
    Convert xpaths to extras

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    for k, v in data[key].iteritems():
        extras.append({'key': k, 'value': v})


def convert_languages(key, data, errors, context):
    '''
    Convert ISO 639 language abbreviations to ISO 639-2 T.
    data['key'] may be a string with comma separated values or a single language code.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''

    value = data.get(key)

    if not isinstance(value, basestring):
        return

    new_languages = []

    for lang in value.split(','):
        lang = lang.strip().lower()
        if lang:
            try:
                languages.get(part2b=lang)
                new_languages.append(lang)
            except KeyError:
                try:
                    languages.get(part3=lang)
                    new_languages.append(lang)
                except KeyError:
                    try:
                        # Convert two character language codes
                        lang_object = languages.get(part1=lang)
                        new_languages.append(lang_object.part2t)
                    except KeyError as ke:
                        errors[key].append(_('Language %s not in ISO 639-2 T format') % lang)
                        # We could still try to convert from ISO 639-2 B if it shows up somewhere

    if new_languages:
        data[key] = ', '.join(new_languages)


def from_extras_json(key, data, errors, context):
    '''
    Convert a field from JSON format in extras to data_dict.
    The `key` parameter is the field where to save values, so we need to search data_dict to find the correct
    value which we are converting.

    :param key: key for example `('pids',)`
    :param data: data, contains value somewhere, like `('extras', 5, 'value')`
    :param errors: validation errors
    :param context: context
    '''
    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key' and data[k] == key[0]:
            data[key] = json.loads(data[(k[0], k[1], 'value')])
            data.pop(('extras', k[1], 'key'), None)
            data.pop(('extras', k[1], 'value'), None)
            data.pop(('extras', k[1], '__extras'), None)


def to_extras_json(key, data, errors, context):
    '''
    Convert a field to JSON format and store in extras.
    '''
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    extras.append({'key': key[0], 'value': json.dumps(data[key])})


def flattened_to_extras(key, data, errors, context):
    '''
    Convert a flattened key-value pair from data_dict to extras.
    For example `(pids, 0, provider)` -> `extras['pids_0_provider']`.

    .. note::
       The key-value pairs to convert are before CKAN's flattening in format
       pids: [{ id: 'some pid', type: 'data', ...},{ id: 'other pid', type: 'data', ...}]

    .. note::
       From WUI this may create gaps in indexing as those indexes with empty contents are not being sent from the
       HTML form. For example, you may end up having indexes 0, 1, 3, 4, 6 in DB. This will be padded in
       flattened_from_extras by creating empty dicts for those indexes.

    :param key: key, for example `(pids, 0, provider)`
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras

    if data[key]:
        extras.append({'key': "%s_%s_%s" % key, 'value': data[key]})


def flattened_from_extras(key, data, errors, context):
    '''
    Convert a whole bunch of flattened key-value pairs from extras to a list of dicts in data_dict.
    Format in extras must be like `key[0]_index_innerkey`. For example: `pids_02_provider`.

    .. note::
       The list of dicts is padded to the largest index found with empty dicts. WUI may cause gaps in indexing.

    :param key: The key to convert as tuple, for example `('pids',)`
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    destination_key = key[0]    # For example 'pids'

    # make destination a pointer to data-dict
    destination = data.get((destination_key,), [])
    if destination is missing:
        destination = []
    if not destination:
        data[(destination_key,)] = destination

    for k in data.keys():
        if k[0] == 'extras' and k[2] == 'key':
            extras_key = data[k].split('_')
            extras_value = data[(k[0], k[1], 'value')]

            if extras_key[0] == destination_key:
                index = int(extras_key[1])
                destination += [{} for i in range(index - len(destination) + 1)]    # pad destination list with {}'s

                destination[index].update({extras_key[2]: extras_value})

                data.pop((k[0], k[1], 'key'), None)
                data.pop((k[0], k[1], 'value'), None)
                data.pop((k[0], k[1], '__extras'), None)


def default_name_from_id(key, data, errors, context):
    '''
    If name not given, generate name from package.id

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    if not data.get(key):
        id = data.get(('id',))

        data[key] = utils.datapid_to_name(id)


def check_primary_pids(key, data, errors, context):
    '''
    Check that primary pids exist, if not, get them from package.id and package.name

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''

    data_pids = utils.get_pids_by_type('data', {'pids': data.get(('pids',))}, primary=True)

    if not data_pids:
        data[('pids',)].append({'primary': u'True', 'type': 'data', 'id': data[('name',)]})
