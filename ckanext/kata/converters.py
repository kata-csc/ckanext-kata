# coding=utf8
"""
Functions to convert dataset form fields from or to db fields.
"""
import json
from iso639 import languages
from pylons import config

from ckan.lib import helpers as h

import os
import re
import logging
import functools
from pylons.i18n import _
from ckan.lib.navl.dictization_functions import missing, Invalid

from ckan.logic.action.create import related_create
from ckan.model import Related, Session, Group, repo
import ckan.logic as logic

from ckanext.kata import settings, utils

log = logging.getLogger('ckanext.kata.converters')

UNRESOLVED_LICENSE_ID = u'unresolved_license_id'


def gen_translation_str_from_multilang_field(fieldkey, message, key, data, errors, context):
    '''
    Fetch all the lang* fields e.g. for fieldkey 'title' of type
    ('langtitle', n, 'lang'): u'en',
    ('langtitle', n, 'value'): u'translation'

    and generate a JSON translation string of type
    title: {'en':'translation', 'fi':'kaannos'}

    This converter is called only once for the hidden field
    where the data is then stored.

    :param fieldkey: 'title' or 'notes' currently
    :param message: translation string for parse error message
    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''
    langkey = 'lang' + fieldkey

    # For API requests, we need to validate if the
    # data is already given in the new format, and
    # no lang* fields given. In that case, do nothing.
    if data.get((fieldkey,)) and not data.get((langkey, 0, 'lang')):
        json_string = data.get((fieldkey,))

        json_data = {}
        try:
            json_data = json.loads(json_string)
        except (ValueError, TypeError):
            errors[key].append(message)

        # we also need to validate the keys:
        try:
            for k in json_data.keys():
                if k == "undefined":    # some harvesters don't have languages defined
                    continue
                try:
                    languages.get(part3=k)
                except KeyError:
                    errors[key].append(_('The language code is not in ISO639-3 format'))
        except AttributeError:
            errors[key].append(_("The given {field} string is incorrectly formatted".format(field=fieldkey)))

        return

    json_data = {}

    # loop through all the translations
    i = 0
    while data.get((langkey, i, 'lang'), []):
        lval = data[(langkey, i, 'lang')]
        rval = data[(langkey, i, 'value')]
        if rval:    # skip a language without translation
            json_data[lval] = rval
        i += 1

    if json_data:
        data[(fieldkey,)] = json.dumps(json_data)


def gen_translation_str_from_langtitle(key, data, errors, context):
    return gen_translation_str_from_multilang_field('title', _('The given title string is not JSON parseable'),
                                                    key, data, errors, context)


def gen_translation_str_from_langnotes(key, data, errors, context):
    return gen_translation_str_from_multilang_field('notes', _('The given description string is not JSON parseable'),
                                                    key, data, errors, context)


def ensure_valid_notes(key, data, errors, context):
    '''
    Converts the notes field into a JSON string if it isn't already.
    '''
    field = data.get(('notes',))
    try:
        json.loads(field)
    except (ValueError, TypeError):
        data[('notes',)] = json.dumps({'und': field})


def set_language_for_title(key, data, errors, context):
    '''
    Some harvested datasets don't have title language attribute. Set it to Finnish
    as we know it should be it.

    :param key: key
    :param data: data
    :param errors: errors
    :param context: context
    '''

    field = data.get(key)
    try:
        jsn = json.loads(field)
        for k in jsn.keys():
            if len(k) < 1 and not jsn.get('fin'):
                jsn['fin'] = jsn.get(k)
                del jsn['']
        data[('title',)] = json.dumps(jsn)
    except:
        log.debug('Setting default language to title did not finish')


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


def escape_quotes(key, data, errors, context):
    '''
    Escape double quotes, so that we can store the title in json

    :param key: key
    :param data: data
    :param errors: errors
    :param context: context
    '''

    data[key] = data.get(key).replace('"', '\\"')


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
    if data.get(key):
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
    Convert ISO 639-2 B and 639-3 language abbreviations to ISO 639-2 T.
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
    In all cases, generate name from package.id

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''

    data[key] = utils.pid_to_name(data.get(('id',)))


def to_license_id(key, data, errors, context):
    '''
    Try to match license to existing defined license, replace matched content with license id.

    If license_id is unresolvable (key exists but value not recognized), make license_id = 'other'.
    Set also a temporary variable for license URL converter (in case it has not been run already)
    that contains the original license id value.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''

    license_id_out = resolve_license_id(data.get(key))
    if license_id_out == UNRESOLVED_LICENSE_ID:
        data[UNRESOLVED_LICENSE_ID] = data.get(key)
        data[key] = u'other'
    else:
        data[key] = license_id_out


def resolve_license_id(license_id):
    '''
    The license converter is divided into two parts: the 'fuzzy' part and the lookup table part.
    We will first try to check whether the license fits into any of the Creative Commons licenses
    by trying to find certain keywords (i.e. 'cc', 'by', 'nd' etc.).

    If the license wasn't of type CC, it is compared to the lookup table of known licenses in
    license_id_map.json.

    :param license_id: license_id to resolve
    :return: resolved license_id
    '''

    map_file_name = os.path.dirname(os.path.realpath(__file__)) + '/license_id_map.json'
    license_id_out = None
    license_id_work = None

    # Part 1: fuzzy search for Creative Common licenses
    if license_id:
        license_id_lower = license_id.lower().strip()
        if 'cc' in license_id_lower or ('creative' in license_id_lower and 'commons' in license_id_lower):
            if 'by' in license_id_lower or 'attribution' in license_id_lower:
                if 'nc' in license_id_lower or 'noncommercial' in license_id_lower:
                    if 'sa' in license_id_lower or 'sharealike' in license_id_lower:
                        license_id_work = 'CC-BY-NC-SA'
                    elif 'nd' in license_id_lower or 'nonderivative' in license_id_lower:
                        license_id_work = 'CC-BY-NC-ND'
                    else:
                        license_id_work = 'CC-BY-NC'
                elif 'nd' in license_id_lower or 'nonderivative' in license_id_lower:
                    license_id_work = 'CC-BY-ND'
                elif 'sa' in license_id_lower or 'sharealike' in license_id_lower:
                    license_id_work = 'CC-BY-SA'
                else:
                    license_id_work = 'CC-BY'

            # Try to figure out the Creative Commons version
            if license_id_work:
                if '1' in license_id_lower:
                    license_id_out = license_id_work + "-1.0"
                elif '2' in license_id_lower:
                    license_id_out = license_id_work + "-2.0"
                elif '3' in license_id_lower:
                    license_id_out = license_id_work + "-3.0"
                elif '4' in license_id_lower:
                    license_id_out = license_id_work + "-4.0"
                else:
                    log.debug("CC-license found, but no version number given")

            # CC-Zero license
            if 'cc0' in license_id_lower or 'zero' in license_id_lower:
                license_id_out = 'CC0-1.0'
        if license_id_out:
            log.debug("--> " + license_id_out)
            return license_id_out
        else:

            # Part 2: compare the licenses to license_id_map.json lookup
            with open(map_file_name) as map_file:
                license_map = json.load(map_file)

            license_id_out = license_map.get(license_id_lower)
            if license_id_out:
                log.debug("--> license_id_map.json: " + license_id_out)
                return license_id_out
            else:
                # no matching license found, return unresolved
                log.debug("No license ID in license collection")
                return UNRESOLVED_LICENSE_ID
    else:
        log.debug("No license ID in data")
        return "undefined"



def to_relation(key, data, errors, context):
    '''
    Try to match relation to existing defined relation, replace matched content with relation id.

    :param key: key
    :param data: data
    :param errors: validation errors
    :param context: context
    '''

    relation_id = data.get(key)
    log.debug("relation: " + relation_id)
    if relation_id:
        map_file_name = os.path.dirname(os.path.realpath(__file__)) + '/theme/public/relations.json'
        with open(map_file_name) as map_file:
            relation_map = json.load(map_file)

        relation_id_out = None
        for relation in relation_map:
            if relation.get('id').lower() == relation_id.lower().strip():
                relation_id_out = relation.get('id')
                log.debug("Resulting relation id: " + data[key])
                break

        if relation_id_out:
            data[key] = relation_id_out
        else:
            # no matching relation found, do nothing
            log.debug("No existing relation ID matched relation")

def populate_license_URL_if_license_id_not_resolved(key, data, errors, context):
    '''
     This function modifies license_URL value in case license_id is not recognized.

     If license id converter (to_license_id) has been run AND license id was not
     recognized, a temporary variable in the data dict containing the license id is
     prepended to the value of license URL. The temporary variable is used since
     at this point the real license id entry has already been changed to value 'other'.

     If license id converter (to_license_id) has not been run AND license id is not
     recognized, this function should change license URL to include the license id.

    :param key:
    :param data:
    :param errors:
    :param context:
    :return:
    '''

    if data.get(UNRESOLVED_LICENSE_ID) and data.get(('license_id',)) == u'other':
        data[key] = data.get(UNRESOLVED_LICENSE_ID) + ('. ' + data.get(key) if data.get(key) else '')
    elif resolve_license_id(data.get(('license_id',))) == UNRESOLVED_LICENSE_ID:
        data[key] = data.get(('license_id',)) + '. ' + data.get(key) if data.get(key) else data.get(('license_id',))