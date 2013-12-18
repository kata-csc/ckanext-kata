# pylint: disable=unused-argument

"""
Functions to convert dataset form fields from or to db fields.
"""
import pycountry

from pylons import h

import re
import logging
from pylons.i18n import _
from ckan.lib.navl.validators import missing

from ckan.logic.action.create import related_create
from ckan.model import Related, Session, Group, repo
from ckan.model.authz import setup_default_user_roles

from ckanext.kata import settings, utils

log = logging.getLogger('ckanext.kata.converters')


def pid_from_extras(key, data, errors, context):
    '''
    Get version_PID from extras or generate a new one.
    '''
    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key' and data[k] == 'version_PID':
            data[('version_PID',)] = data[(k[0], k[1], 'value')]

    if not ('version_PID',) in data:
        data[('version_PID',)] = utils.generate_pid()


def org_auth_to_extras(key, data, errors, context):
    '''
    Convert author and organization to extras
    '''
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    if len(data[key]) > 0:
        if key[0] == 'orgauth':
            if not ('orgauth', key[1], 'org') in data or len(data[('orgauth', key[1], 'org')]) == 0:
                errors[key].append(_('Organisation is missing'))
            if not ('orgauth', key[1], 'value') in data or len(data[('orgauth', key[1], 'value')]) == 0:
                errors[key].append(_('Author is missing'))

        oval = data[(key[0], key[1], 'org')]

        extras.append({'key': "author_%s" % key[1],
                      'value': data[key]})
        extras.append({'key': 'organization_%s' % key[1],
                       'value': oval
                       })

def org_auth_to_extras_oai(key, data, errors, context):
    '''
    Convert author and organization to extras
    '''
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    if len(data[key]) > 0:
        if key[0] == 'orgauth':
            # Todo, this is not needed, requires replanning
            if (not ('orgauth', key[1], 'org') in data or len(data[('orgauth', key[1], 'org')]) == 0) and \
            (not ('orgauth', key[1], 'value') in data or len(data[('orgauth', key[1], 'value')]) == 0):
                errors[key].append(_('Author and organization is missing'))

        oval = data[(key[0], key[1], 'org')]

        extras.append({'key': "author_%s" % key[1],
                      'value': data[key]})
        extras.append({'key': 'organization_%s' % key[1],
                       'value': oval
                       })


def org_auth_from_extras(key, data, errors, context):
    '''
    Convert (author, organization) pairs from package.extra to 'orgauths' dict
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

            if re.search('^(organization_)\d+$', data[k]):
                val = data[(k[0], k[1], 'value')]
                org = {'key': data[k], 'org': val}
                if org not in orgs:
                    orgs.append(org)
    orgs = sorted(orgs, key=lambda ke: int(ke['key'].rsplit('_', 1)[1]))
    authors = sorted(authors, key=lambda ke: int(ke['key'].rsplit('_', 1)[1]))
    for org, author in zip(orgs, authors):
        orgauth = {}
        orgauth.update({'value': author['value']})
        orgauth.update({'org': org['org']})
        if not orgauth in orgauths:
            orgauths.append(orgauth)


def ltitle_to_extras(key, data, errors, context):
    '''
    Convert title & language pair from dataset form to db format and validate.
    Title & language pairs will be stored in package_extra.
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

            if re.search('^(lsel|lang_title_)\d+$', data[k]):
                val = data[(k[0], k[1], 'value')]
                lang = {'key': data[k], 'lang': val}
                if lang not in langs:
                    langs.append(lang)
    langs = sorted(langs, key=lambda ke: int(ke['key'].rsplit('_', 1)[1]))
    titles = sorted(titles, key=lambda ke: int(ke['key'].rsplit('_', 1)[1]))
    for lang, title in zip(langs, titles):
        langtitle = {}
        langtitle.update({'value': title['value']})
        langtitle.update({'lang': lang['lang']})
        if not langtitle in langtitles:
            langtitles.append(langtitle)



def event_to_extras(key, data, errors, context):
    '''
    Parses separate 'ev*' parameters from 'data' data_dict to 'extra' field
    in that same 'data'.
    @param key: key from schema, 'evtype', 'evdescr' etc.
    @param data: whole data_dict passed for modification
    '''
    #log.debug("event_to_extras(): key: %s : %s", str(key), str(data[key]))

    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    if key[2] == 'value' and len(data[key]) > 0 and type(data[key]) == unicode:
        extras.append({'key': "%s_%d" % (key[0], key[1]),
                       'value': data[key]})

def event_from_extras(evkey, data, errors, context):
    if not ('events',) in data:
        data[('events',)] = []
    types = []
    whos = []
    whens = []
    descrs = []
    events = data[('events',)]

    #evvalues = []

    log.debug("event_FROM_extras(key, ...): evkey: %s" % str(evkey))

    # TODO: rewrite to extract each key:value with its key's validator
    #for k in data.keys():
    #    if k[0] == 'extras' and k[-1] == 'key':
    #        if evkey[0] in data[k]:
    #            # evindex = int(data[k].split('_')[-1])
    #            val = data[(k[0], k[1], 'value')]
    #            if not {'key': data[k], 'value': val} in evvalues:
    #            evvalues.append({'key': data[k], 'value': val})

    #evvalues = sorted(evvalues, key=lambda evdict: int(evdict['key'].split('_')[-1]))

    for k in data.keys():
        if k[0] == 'extras' and k[-1] == 'key':
            if 'evtype' in data[k]:
                val = data[(k[0], k[1], 'value')]
                type = {'key': data[k]}
                type['value'] = val
                if not {'key': data[k], 'value': val} in types:
                    types.append(type)
            if 'evwho' in data[k]:
                val = data[(k[0], k[1], 'value')]
                who = {'key': data[k]}
                who['value'] = val
                if not {'key': data[k], 'value': val} in whos:
                    whos.append(who)
            if 'evwhen' in data[k]:
                val = data[(k[0], k[1], 'value')]
                when = {'key': data[k]}
                when['value'] = val
                if not {'key': data[k], 'value': val} in whens:
                    whens.append(when)
            if 'evdescr' in data[k]:
                val = data[(k[0], k[1], 'value')]
                descr = {'key': data[k]}
                descr['value'] = val
                if not {'key': data[k], 'value': val} in descrs:
                    descrs.append(descr)

    types = sorted(types, key=lambda ke: int(ke['key'].split('_')[-1]))
    whos = sorted(whos, key=lambda ke: int(ke['key'].split('_')[-1]))
    whens = sorted(whens, key=lambda ke: int(ke['key'].split('_')[-1]))
    descrs = sorted(descrs, key=lambda ke: int(ke['key'].split('_')[-1]))

    for etype, ewho, ewhen, edescr in zip(types, whos, whens, descrs):
        if not (etype, ewho, ewhen, edescr) in events:
            events.append((etype, ewho, ewhen, edescr))


def export_as_related(key, data, errors, context):
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
    If langdis == 'True', remove all languages.

    Expecting language codes in data['key'].
    '''
    langdis = data.get(('langdis',))

    langs = data.get(key).split(',')

    if langdis == 'False':
        # Language enabled

        if langs == [u'']:
            errors[key].append(_('No language given.'))
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
    Convert all extras fields from extras to data dict and remove
    fields from extras. Removal helps counter IndexError with unflatten after
    validation.
    '''
    if data.get(('extras',)) is missing:
        return
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    for k in data.keys():
        if k[-1] in settings.KATA_FIELDS:
            if not {'key': k[-1], 'value': data[k]} in extras:
                extras.append({'key': k[-1], 'value': data[k]})

def xpath_to_extras(key, data, errors, context):
    '''
    '''
    #log.debug("event_to_extras(): key: %s : %s", str(key), str(data[key]))
    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras
    for k, v in data[key].iteritems():
        extras.append({'key': k, 'value': v})


def convert_languages(key, data, errors, context):
    '''
    Convert ISO 639 language abbreviations to ISO 639-2 T

    data['key'] may be a string with comma separated values or a single language code.
    '''

    value = data.get(key)

    if not isinstance(value, basestring):
        return

    langs = value.split(',')
    new_langs = []

    for lang in langs:
        lang = lang.strip()
        if lang:
            try:
                pycountry.languages.get(terminology=lang)
                new_langs.append(lang)
            except KeyError:
                try:
                    # Convert two character language codes
                    lang_object = pycountry.languages.get(alpha2=lang)
                    new_langs.append(lang_object.terminology)
                except KeyError as ke:
                    errors[key].append(_('Language %s not in ISO 639-2 T format' % lang))
                    # We could still try to convert from ISO 639-2 B if it shows up somewhere

    if new_langs:
        data[key] = ', '.join(new_langs)