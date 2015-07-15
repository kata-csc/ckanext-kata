# coding=utf8
"""
Controllers for Kata.
"""
from cgi import FieldStorage
import datetime
import functionally as fn
import json
import logging
import mimetypes
import rdflib
import re
import string
import urllib2
import sqlalchemy
from sqlalchemy.sql import select
from urllib import urlencode

from lxml import etree

from paste.deploy.converters import asbool
from pylons import config, request, session, g, response
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _
from ckan.controllers.api import ApiController
from ckan.controllers.package import PackageController
from ckan.controllers.user import UserController
from ckan.controllers.storage import StorageController
import ckan.lib.i18n
from ckan.lib.base import BaseController, c, h, redirect, render, abort
from ckan.lib.email_notifications import send_notification
from ckan.lib import captcha, helpers
import ckan.lib.maintain as maintain
from ckan.logic import get_action, NotAuthorized, NotFound, ValidationError
import ckan.logic as logic
import ckan.model as model
from ckan.model import Package, User, meta, Session
from ckan.model.authz import add_user_to_role
import ckan.plugins as plugins
from ckan.common import response
from ckan.common import OrderedDict
import ckan.plugins as p

import ckanext.harvest.interfaces as h_interfaces
from ckanext.kata.model import KataAccessRequest
import ckanext.kata.clamd_wrapper as clamd_wrapper
import ckanext.kata.settings as settings
from ckanext.kata import utils
import ckanext.kata.helpers as kata_helpers
import os
import difflib

_get_or_bust = ckan.logic.get_or_bust
check_access = logic.check_access

log = logging.getLogger(__name__)
t = plugins.toolkit


def get_package_owner(package):
    """Returns the user id of the package admin for the specified package.
       If multiple user accounts are associated with the package as admins,
       an arbitrary one is returned.

       :param package: package data
       :type package: Package object
       :returns: userid
       :rtype: string
    """
    userid = None
    for role in package.roles:
        if role.role == "admin":
            userid = role.user_id
            break
    return userid


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


def url_with_params(url, params):
    params = _encode_params(params)
    return url + u'?' + urlencode(params)


class MetadataController(BaseController):
    '''
    URN export
    '''

    def _urnexport(self):
        '''
        Uncached urnexport, needed for testing.
        '''
        _or_ = sqlalchemy.or_
        _and_ = sqlalchemy.and_

        xmlns = "urn:nbn:se:uu:ub:epc-schema:rs-location-mapping"
        def locns(loc):
            return "{%s}%s" % (xmlns, loc)
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemalocation = "urn:nbn:se:uu:ub:epc-schema:rs-location-mapping " \
                         "http://urn.kb.se/resolve?urn=urn:nbn:se:uu:ub:epc-schema:rs-location-mapping&godirectly"
        records = etree.Element("{" + xmlns + "}records",
                         attrib={"{" + xsi + "}schemaLocation": schemalocation},
                         nsmap={'xsi': xsi, None: xmlns})

        # Gather all package id's that might contain a Kata/IDA data PID
        query = model.Session.query(model.PackageExtra).filter(model.PackageExtra.key.like('pids_%_id')). \
            filter(model.PackageExtra.value.like('urn:nbn:fi:csc-%')). \
            join(model.Package).filter(model.Package.private == False).filter(model.Package.state == 'active'). \
            values('package_id')

        base_url = config.get('ckan.site_url', '').strip("/")

        prot = etree.SubElement(records, locns('protocol-version'))
        prot.text = '3.0'
        datestmp = etree.SubElement(records, locns('datestamp'), attrib={'type': 'modified'})
        now = datetime.datetime.now().isoformat()
        datestmp.text = now
        for pkg_id, in set(query):
            data_dict = get_action('package_show')({}, {'id': pkg_id})
            # Get primary data PID and make sure we want to display this dataset
            try:
                data_pid = utils.get_pids_by_type('data', data_dict, primary=True)[0].get('id', '')
            except IndexError:
                continue
            if data_pid.startswith('urn:nbn:fi:csc-'):
                record = etree.SubElement(records, locns('record'))
                header = etree.SubElement(record, locns('header'))
                datestmp = etree.SubElement(header, locns('datestamp'), attrib={'type': 'modified'})
                datestmp.text = now
                identifier = etree.SubElement(header, locns('identifier'))
                identifier.text = data_pid
                destinations = etree.SubElement(header, locns('destinations'))
                destination = etree.SubElement(destinations, locns('destination'), attrib={'status': 'activated'})
                datestamp = etree.SubElement(destination, locns('datestamp'), attrib={'type': 'activated'})
                url = etree.SubElement(destination, locns('url'))
                url.text = "%s%s" % (base_url,
                                 helpers.url_for(controller='package',
                                           action='read',
                                           id=data_dict.get('name')))
        response.content_type = 'application/xml; charset=utf-8'
        return etree.tostring(records, encoding="UTF-8")

    @beaker_cache(type="dbm", expire=86400)
    def urnexport(self):
        '''
        Generate an XML listing of packages, which have Kata or Ida URN as data PID.
        Used by a third party service.

        :returns: An XML listing of packages and their URNs
        :rtype: string (xml)
        '''
        return self._urnexport()


class KATAApiController(ApiController):
    '''
    Functions for autocomplete fields in add dataset form
    '''

    @beaker_cache(type="dbm", expire=30, invalidate_on_startup=True)
    def _get_funders(self):
        records = model.Session.execute("select distinct second.value from package_extra as first \
            left join package_extra as second on first.package_id = second.package_id and second.key =  'agent_' || substring(first.key from 'agent_(.*)_role') || '_organisation' \
            where first.key like 'agent%role' and first.value = 'funder' and first.state='active'")
        url = config.get("ckanext.kata.funder_url", None) or "file://%s" % os.path.abspath(os.path.join(os.path.dirname(__file__), "theme/public/funder.json"))
        source = urllib2.urlopen(url)
        try:
            return ["%s - %s" % (funder['fi'], funder['en']) for funder in json.load(source)] + [result[0] for result in records]
        finally:
            source.close()

    def funder_autocomplete(self):
        query = request.params.get('incomplete', '').lower()
        limit = request.params.get('limit', 10)

        matches = sorted([funder for funder in self._get_funders() if funder and string.find(funder.lower(), query) != -1],
                         key=lambda match: (match.lower().startswith(query), difflib.SequenceMatcher(None, match.lower(), query).ratio()),
                         reverse=True)[0:limit]
        resultSet = {
            'ResultSet': {
                'Result': [{'Name': tag} for tag in matches]
            }
        }
        return self._finish_ok(resultSet)

    def media_type_autocomplete(self):
        '''
        Suggestions for mimetype

        :rtype: dictionary
        '''
        query = request.params.get('incomplete', '')
        known_types = set(mimetypes.types_map.values())
        matches = [ type_label for type_label in known_types if string.find(type_label, query) != -1 ]
        matches = sorted(matches)
        result_set = {
            'ResultSet': {
                'Result': [{'Name': label} for label in matches]
            }
        }
        return self._finish_ok(result_set)

    def tag_autocomplete(self):
        '''
        Suggestions for tags (keywords)

        :rtype: dictionary
        '''

        query = request.params.get('incomplete', '')
        language = request.params.get('language', '')

        return self._onki_autocomplete_uri(query, "koko", language)

    def discipline_autocomplete(self):
        '''
        Suggestions for discipline

        :rtype: dictionary
        '''

        query = request.params.get('incomplete', '')
        language = request.params.get('language', '')

        return self._onki_autocomplete_uri(query, "okm-tieteenala", language)

    def location_autocomplete(self):
        '''
        Suggestions for spatial coverage

        :rtype: dictionary
        '''
        query = request.params.get('incomplete', '')
        language = request.params.get('language', '')

        return self._onki_autocomplete(query, "paikat")

    def _query_finto(self, query, vocab, language=None):
        '''
        Queries Finto ontologies by returning the whole result set, which can
        be parsed according to the needs (see _onki_autocomplete_uri)

        :param query: the string to search for
        :type query: string
        :param vocab: the vocabulary/ontology, i.e. lexvo
        :type vocab: string
        :param language: the language of the query
        :type query: string

        :rtype: dictionary
        '''

        url_template = "http://api.finto.fi/rest/v1/search?query={q}*&vocab={v}"

        if language:
            url_template += "&lang={l}"

        jsondata = {}

        if query:
            try:
                url = url_template.format(q=query, v=vocab, l=language)
            except UnicodeEncodeError:
                url = url_template.format(q=query.encode('utf-8'), v=vocab, l=language)

            data = urllib2.urlopen(url).read()
            jsondata = json.loads(data)

        return jsondata


    def _onki_autocomplete(self, query, vocab, language=None):
        '''
        Queries the remote ontology for suggestions and
        formats the data.

        :param query: the string to search for
        :type query: string
        :param vocab: the vocabulary/ontology
        :type vocab: string
        :param language: the language of the query
        :type query: string

        :rtype: dictionary
        '''
        jsondata = self._query_finto(query, vocab, language)
        labels = []

        if u'results' in jsondata:
            results = jsondata['results']
            labels = [concept.get('prefLabel', '').encode('utf-8') for concept in results]

        result_set = {
            'ResultSet': {
                'Result': [{'Name': label} for label in labels]
            }
        }

        return self._finish_ok(result_set)

    def _onki_autocomplete_uri(self, query, vocab, language=None):
        '''
        Queries the remote ontology for suggestions and
        formats the data, suggests uri's. Returns uri as key and
        label as name.

        :param query: the string to search for
        :type query: string
        :param vocab: the vocabulary/ontology
        :type vocab: string
        :param language: the language of the query
        :type query: string

        :rtype: dictionary
        '''

        jsondata = self._query_finto(query, vocab, language)
        labels = []

        if u'results' in jsondata:
            results = jsondata['results']
            labels = [(concept.get('prefLabel', '').encode('utf-8'), concept['uri'].encode('utf-8')) for concept in results]

        result_set = [{'key': l[1], 'label': l[0], 'name': l[0]} for l in labels]

        return self._finish_ok(result_set)

    # TODO Juho: Temporary organisation autocomplete implementation in
    # kata..plugin.py, kata..controllers.py, kata/actions.py, kata/auth_functions.py
    #  @jsonp.jsonpify
    def organization_autocomplete(self):
        q = request.params.get('incomplete', '')
        limit = request.params.get('limit', 20)
        organization_list = []

        if q:
            context = {'user': c.user, 'model': model}
            data_dict = {'q': q, 'limit': limit}
            organization_list = get_action('organization_autocomplete')(context, data_dict)
        return self._finish_ok(organization_list)

    def language_autocomplete(self):
        '''
        Suggestions for languages.

        :rtype: dictionary
        '''

        language = request.params.get('language', '')
        query = request.params.get('incomplete', '')

        jsondata = self._query_finto(query, "lexvo", language)
        labels = []

        if u'results' in jsondata:
            results = jsondata['results']
            labels = [(concept.get('prefLabel', '').encode('utf-8'), concept['localname'].encode('utf-8')) for concept in results]

        result_set = [{'key': l[1], 'label': l[0], 'name': l[0]} for l in labels]

        return self._finish_ok(result_set)


class EditAccessRequestController(BaseController):
    '''
    EditAccessRequestController class provides a feature to ask
    for editor rights to a dataset. On the other hand,
    it also provides the process to grant them upon request.
    '''

    def _have_pending_requests(self, pkg_id, user_id):
        """
        Returns whether there are already pending requests
        from the given user regarding the given package.

        :param pkg_id: package id
        :type pkg_id: string
        :param user_id: user id
        :type user_id: string

        :rtype: boolean
        """

        pending_requests = model.Session.query(KataAccessRequest).filter(
            KataAccessRequest.pkg_id == pkg_id, KataAccessRequest.user_id == user_id)
        return pending_requests.count() > 0

    def create_request(self, pkg_id):
        """
        Creates a new editor access request in the database.
        Redirects the user to dataset view page

        :param pkg_id: package id
        :type pkg_id: string
        """

        url = h.url_for(controller='package', action='read', id=pkg_id)

        pkg = Package.get(pkg_id)
        if not pkg:
            abort(404, _("Dataset not found"))

        pkg_title = pkg.title if pkg.title else pkg.name

        user = c.userobj if c.userobj else None
        if user:
            if not self._have_pending_requests(pkg_id, user.id):
                req = KataAccessRequest(user.id, pkg.id)
                req.save()
                h.flash_success(_("A request for editing privileges will be sent to the administrator of package %s") % kata_helpers.get_translation(pkg_title))
                redirect(url)
            else:
                h.flash_error(_("A request is already pending"))
                redirect(url)
        else:
            h.flash_error(_("You must be logged in to request edit access"))
            redirect(url)

    def unlock_access(self, id):
        '''
        Adds a user to role editor for a dataset and
        redirects the user to dataset view page

        :param id: package id
        :type id: string
        '''
        q = model.Session.query(KataAccessRequest)
        q = q.filter_by(id=id)
        req = q.first()
        if req:
            user = User.get(req.user_id)
            pkg = Package.get(req.pkg_id)
            pkg_title = pkg.title if pkg.title else pkg.name
            add_user_to_role(user, 'editor', pkg)
            url = h.url_for(controller='package', action='read', id=req.pkg_id)
            h.flash_success(_("%s now has editor rights to package %s") % (user.name, pkg_title))
            req.delete()
            meta.Session.commit()
            redirect(url)
        else:
            h.flash_error(_("No such request found!"))
            redirect('/')

    def render_edit_request(self, pkg_id):
        """
        Renders a page for requesting editor access to the dataset.
        """

        url = h.url_for(controller='package', action='read', id=pkg_id)

        c.package = Package.get(pkg_id)
        if not c.package:
            abort(404, _("Dataset not found"))

        c.package_owner = get_package_owner(c.package)
        user = c.userobj if c.userobj else None

        if user:
            if not self._have_pending_requests(pkg_id, user.id):
                return render('contact/edit_request_form.html')
            else:
                h.flash_error(_("A request is already pending"))
                redirect(url)
        else:
            h.flash_error(_("You must be logged in to request edit access"))
            redirect(url)


class ContactController(BaseController):
    """
    Add features to contact the dataset's owner.

    From the web page, this can be seen from the link telling that this dataset is accessible by contacting the author.
    The feature provides a form for message sending, and the message is sent via email.
    """

    def _get_logged_in_user(self):
        if c.userobj:
            name = c.userobj.fullname if c.userobj.fullname else c.userobj.name
            email = c.userobj.email
            return {'name': name, 'email': email}
        else:
            return None

    def _get_contact_email(self, pkg_id, contact_id):
        recipient = None
        if contact_id:
            contacts = utils.get_package_contacts(pkg_id)
            contact = fn.first(filter(lambda c: c.get('id') == contact_id, contacts))

            if contact and 'email' in contact.keys():
                email = contact.get('email')
                name = contact.get('name')
                recipient = {'name': name, 'email': email}

        return recipient

    def _mark_package_as_contacted(self, userobj, pkg_id):
        """Mark this user as having already emailed the contact person of the package."""

        model.repo.new_revision()

        if "contacted" not in userobj.extras:
            userobj.extras['contacted'] = []

        userobj.extras['contacted'].append(pkg_id)
        userobj.save()

    def _has_already_contacted(self, userobj, pkg_id):
        return pkg_id in userobj.extras.get('contacted', [])

    def _send_message(self, subject, message, recipient_email, recipient_name=None):
        email_dict = {'subject': subject,
                      'body': message}

        if not recipient_name:
            # fall back to using the email address as the name of the recipient
            recipient_name = recipient_email

        recipient_dict = {'display_name': recipient_name, 'email': recipient_email}

        if c.user and message:
            send_notification(recipient_dict, email_dict)

    def _prepare_and_send(self, pkg_id, recipient_id, subject, prefix_template, suffix):
        """
        Sends a message by email from the logged in user to the appropriate
        contact address of the given dataset.

        The prefix template should have formatting placeholders for the following arguments:
        {sender_name}, {sender_email}, {package_title}, {data_pid}

        :param pkg_id: package id
        :type pkg_id: string
        :param recipient_id: id of the recipient, as returned by utils.get_package_contacts
        :type recipient_id: string
        :param subject: the subject of the message
        :type subject: string
        :param prefix_template: the template for the prefix to be automatically included before the user message
        :type prefix_template: unicode
        :param suffix: an additional note to be automatically included after the user message
        :type suffix: unicode
        """

        package = Package.get(pkg_id)
        package_title = package.title if package.title else package.name

        sender = self._get_logged_in_user()
        recipient = self._get_contact_email(pkg_id, recipient_id)

        if not recipient:
            abort(404, _('Recipient not found'))

        user_msg = request.params.get('msg', '')

        if sender:
            if user_msg:
                if not self._has_already_contacted(c.userobj, pkg_id):
                    prefix = prefix_template.format(
                        sender_name=sender['name'],
                        sender_email=sender['email'],
                        package_title=package_title,
                        data_pid=utils.get_primary_data_pid_from_package(package)
                    )

                    full_msg = u"{a}{b}{c}".format(a=prefix, b=user_msg, c=suffix)
                    self._send_message(subject, full_msg, recipient.get('email'), recipient.get('name'))
                    self._mark_package_as_contacted(c.userobj, pkg_id)
                    h.flash_success(_("Message sent"))
                else:
                    h.flash_error(_("Already contacted"))
            else:
                h.flash_error(_("No message"))
        else:
            h.flash_error(_("Please login"))

        url = h.url_for(controller='package', action='read', id=pkg_id)

        return redirect(url)

    def send_contact_message(self, pkg_id):
        """
        Sends a message by email from the logged in user to the appropriate
        contact address of the dataset.

        :param pkg_id: package id
        :type pkg_id: string
        """

        package = Package.get(pkg_id)
        package_title = package.title if package.title else package.name
        subject = u"Message regarding dataset / Viesti koskien tietoaineistoa %s" % package_title
        recipient_id = request.params.get('recipient', '')

        return self._prepare_and_send(pkg_id, recipient_id, subject, settings.USER_MESSAGE_PREFIX_TEMPLATE, settings.REPLY_TO_SENDER_NOTE)

    def send_request_message(self, pkg_id):
        """
        Sends a data request message by email from the logged in user to the appropriate
        contact address of the dataset.

        :param pkg_id: package id
        :type pkg_id: string
        """

        package = Package.get(pkg_id)
        package_title = package.title if package.title else package.name
        subject = u"Data access request for dataset / Datapyyntö tietoaineistolle %s" % package_title
        recipient_id = request.params.get('recipient', '')

        return self._prepare_and_send(pkg_id, recipient_id, subject, settings.DATA_REQUEST_PREFIX_TEMPLATE, settings.REPLY_TO_SENDER_NOTE)

    def render_contact_form(self, pkg_id):
        """
        Render the contact form if allowed.

        :param pkg_id: package id
        :type pkg_id: string
        """

        c.package = Package.get(pkg_id)

        if not c.package:
            abort(404, _("Dataset not found"))

        contacts = utils.get_package_contacts(c.package.id)
        c.recipient_options = [ {'text': contact['name'], 'value': contact['id']} for contact in contacts ]
        c.recipient_index = request.params.get('recipient', '')

        url = h.url_for(controller='package',
                        action="read",
                        id=c.package.name)
        if c.user:
            if pkg_id not in c.userobj.extras.get('contacted', []):
                return render('contact/contact_form.html')
            else:
                h.flash_error(_("Already contacted"))
                return redirect(url)
        else:
            h.flash_error(_("Please login"))
            return redirect(url)

    def render_request_form(self, pkg_id):
        """
        Render the access request contact form if allowed.

        :param pkg_id: package id
        :type pkg_id: string
        """

        c.package = Package.get(pkg_id)

        if not c.package:
            abort(404, _("Dataset not found"))

        contacts = utils.get_package_contacts(c.package.id)
        c.recipient_options = [ {'text': contact['name'], 'value': contact['id']} for contact in contacts ]
        c.recipient_index = request.params.get('recipient', '')

        url = h.url_for(controller='package',
                        action="read",
                        id=c.package.name)
        if c.user:
            if pkg_id not in c.userobj.extras.get('contacted', []):
                return render('contact/dataset_request_form.html')
            else:
                h.flash_error(_("Already contacted"))
                return redirect(url)
        else:
            h.flash_error(_("Please login"))
            return redirect(url)


class KataUserController(UserController):
    """
    Overwrite logged_in function in the super class.
    """

    def logged_in(self):
        """Minor rewrite to redirect the user to the own profile page instead of
        the dashboard.
        """
        # we need to set the language via a redirect
        lang = session.pop('lang', None)
        session.save()
        came_from = request.params.get('came_from', '')

        # we need to set the language explicitly here or the flash
        # messages will not be translated.
        ckan.lib.i18n.set_lang(lang)

        if h.url_is_local(came_from):
            return h.redirect_to(str(came_from))

        if c.user:
            context = {'model': model,
                       'user': c.user}

            data_dict = {'id': c.user}

            user_dict = get_action('user_show')(context, data_dict)

            #h.flash_success(_("%s is now logged in") %
            #                user_dict['display_name'])
            return h.redirect_to(controller='user', action='read', id=c.userobj.name)
        else:
            err = _('Login failed. Bad username or password.')
            if g.openid_enabled:
                err += _(' (Or if using OpenID, it hasn\'t been associated '
                         'with a user account.)')
            if asbool(config.get('ckan.legacy_templates', 'false')):
                h.flash_error(err)
                h.redirect_to(controller='user',
                              action='login', came_from=came_from)
            else:
                return self.login(error=err)

    def logged_out_page(self):
        """ Redirect user to front page and inform user. """
        if not c.user:
            h.flash_notice(_("Successfully logged out."))
        h.redirect_to(controller='home', action='index')


class KataPackageController(PackageController):
    """
    Dataset handling modifications and additions.
    """

    def dataset_editor_manage(self, name):
        '''
        Manages (adds) editors and admins of a dataset and sends an invitation email
        if wanted in case user has not yet logged in to the service.
        The invitation email feature has no automatic features bound to it, it is a
        plain email sender.

        :param name: package name
        :type name: string
        :param username: if username (request.param) and role (request.param) are set, the user is added for the role
        :type username: string
        :param role: if username (request.param) and role (request.param) are set, the user is added for the role
        :type role: string
        :param email: if email address (request.param) is given, an invitation email is sent
        :type email: string

        Renders the package_administration page via :meth:`_show_dataset_role_page`

        '''
        context = {'model': model, 'session': model.Session, 'user': c.user}

        if not h.check_access('package_update', {'id': name }):
            h.flash_error(_('Not authorized to see this page'))
            h.redirect_to(controller='package', action='read', id=name)

        data_dict = {}
        data_dict['name'] = name

        username = request.params.get('username', False)
        email = request.params.get('email', False)
        role = request.params.get('role', False)

        pkg = model.Package.get(name)
        data_dict = get_action('package_show')(context, {'id': pkg.id})

        if username:
            data_dict['role'] = role
            data_dict['username'] = username
            try:
                ret = get_action('dataset_editor_add')(context, data_dict)
                h.flash_success(ret)
            except ValidationError as e:
                h.flash_error(e.error_dict.get('message', ''))
            except NotAuthorized:
                error_message = _('No sufficient privileges to add a user to role %s.') % role
                h.flash_error(error_message)
            except NotFound:
                h.flash_error(_('User not found'))

        if email:

            EMAIL_REGEX = re.compile(
    r"""
    ^[\w\d!#$%&\'\*\+\-/=\?\^`{\|\}~]
    [\w\d!#$%&\'\*\+\-/=\?\^`{\|\}~.]+
    @
    [a-z.A-Z0-9-]+
    \.
    [a-zA-Z]{2,6}$
    """,
            re.VERBOSE)
            if isinstance(email, basestring) and email:
                if not EMAIL_REGEX.match(email) or not(asbool(config.get('kata.invitations', True))):
                    if not (asbool(config.get('kata.invitations', True))):
                        error_msg = _(u'Feature disabled')
                    else:
                        error_msg = _(u'Invalid email address')
                    h.flash_error(error_msg)
                else:
                    try:
                        captcha.check_recaptcha(request)
                        try:
                            subject = u'Invitation to use the Etsin - kutsu käyttämään Etsin-palvelua'
                            body = u'\n\n%s would like to add you as an editor for dataset "%s" \
in the Etsin data search service. To enable this, please log in to the service: %s.\n\n' % (c.userobj.fullname, data_dict.get('title', ''), g.site_url)
                            body += u'\n\n%s haluaisi lisätä sinut muokkaajaksi tietoaineistoon "%s" \
Etsin-hakupalvelussa. Mahdollistaaksesi tämän, ole hyvä ja kirjaudu palveluun osoitteessa: %s.\n\n' \
                                    % (c.userobj.fullname, data_dict.get('title', ''), g.site_url)
                            body += u'\n------------\nLähettäjän viesti / Sender\'s message:\n\n%s\n------------\n' % (request.params.get('mail_message', ''))

                            ckan.lib.mailer.mail_recipient(email, email, subject, body)
                            h.flash_success(_('Message sent'))
                            log.info("Invitation sent by %s to %s\n" % (c.userobj.name, email))
                        except ckan.lib.mailer.MailerException:
                            raise
                    except captcha.CaptchaError:
                        error_msg = _(u'Bad Captcha. Please try again.')
                        h.flash_error(error_msg)

        data_dict['domain_object'] = pkg.id
        domain_object_ref = _get_or_bust(data_dict, 'domain_object')
        # domain_object_ref is actually pkg.id, so this could be simplified
        domain_object = ckan.logic.action.get_domain_object(model, domain_object_ref)

        return self._show_dataset_role_page(domain_object, context, data_dict)

    def dataset_editor_delete(self, name):
        '''
        Deletes a user from a dataset role.

        :param name: dataset name
        :type name: string
        :param username: user (request.param) and role (request.param) to be deleted from dataset
        :type username: string
        :param role: user (request.param) and role (request.param) to be deleted from dataset
        :type role: string

        redirects to dataset_editor_manage.
        '''
        context = {'model': model, 'session': model.Session, 'user': c.user}
        data_dict = {}
        data_dict['name'] = name
        data_dict['username'] = request.params.get('username', None)
        data_dict['role'] = request.params.get('role', None)

        try:
            ret = ckan.logic.get_action('dataset_editor_delete')(context, data_dict)
            h.flash_success(ret)

        except ValidationError as e:
            h.flash_error(e.error_dict.get('message', ''))
        except NotAuthorized:
            error_message = _('No sufficient privileges to remove user from role %s.') % data_dict['role']
            h.flash_error(error_message)
        except NotFound:
            h.flash_error(_('User not found'))

        h.redirect_to(controller='ckanext.kata.controllers:KataPackageController',
                                action='dataset_editor_manage', name=name)

    def _roles_list(self, userobj, domain_object):
        '''
        Builds the selection of roles for the role popup menu

        :param userobj: user object
        :param domain_object: dataset domain object
        '''
        if ckan.model.authz.user_has_role(userobj, 'admin', domain_object) or \
                userobj.sysadmin == True:
            return [{'text': 'Admin', 'value': 'admin'},
                    {'text': 'Editor', 'value': 'editor'},
                    {'text': 'Reader', 'value': 'reader'}]
        else:
            return [{'text': 'Editor', 'value': 'editor'},
                    {'text': 'Reader', 'value': 'reader'}]

    def _show_dataset_role_page(self, domain_object, context, data_dict):
        '''
        Adds data for template and renders it

        :param domain_object: dataset domain object
        :param context: context
        :param data_dict: data dictionary
        '''

        c.roles = []
        if c.userobj:
            c.roles = self._roles_list(c.userobj, domain_object)

        editor_list = get_action('roles_show')(context, data_dict)
        c.members = []

        for role in editor_list.get('roles', ''):
            q = model.Session.query(model.User).\
                filter(model.User.id == role['user_id']).first()

            c.members.append({'user_id': role['user_id'], 'user': q.name, 'role': role['role']})
        c.pkg = Package.get(data_dict['id'])
        c.pkg_dict = get_action('package_show')(context, data_dict)

        return render('package/package_rights.html')

    def _upload_xml(self, errors=None, error_summary=None):
        '''
        Allow filling dataset form by parsing a user uploaded metadata file.
        '''
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
        try:
            t.check_access('package_create', context)
        except t.NotAuthorized:
            t.abort(401, _('Unauthorized to upload metadata'))

        xmlfile = u''
        field_storage = request.params.get('xmlfile')
        if isinstance(field_storage, FieldStorage):
            bffr = field_storage.file
            xmlfile = bffr.read()
        url = request.params.get('url', u'')
        xmltype = request.params.get('format', u'')
        log.info('Importing from {src}'.format(
            src='file: ' + field_storage.filename if field_storage else 'url: ' + url))
        for harvester in plugins.PluginImplementations(h_interfaces.IHarvester):
            info = harvester.info()
            if not info or 'name' not in info:
                log.error('Harvester %r does not provide the harvester name in the info response' % str(harvester))
                continue
            if xmltype == info['name']:
                log.debug('_upload_xml: Found harvester for import: {nam}'.format(nam=info['name']))
                try:
                    # TODO: virus check ??
                    if xmlfile:
                        pkg_dict = harvester.parse_xml(xmlfile, context)
                    elif url:
                        pkg_dict = harvester.fetch_xml(url, context)
                    else:
                        h.flash_error(_('Give upload URL or file.'))
                        return h.redirect_to(controller='package', action='new')
                    return super(KataPackageController, self).new(pkg_dict, errors, error_summary)
                except (urllib2.URLError, urllib2.HTTPError):
                    log.debug('Could not fetch from url {ur}'.format(ur=url))
                    h.flash_error(_('Could not fetch from url {ur}'.format(ur=url)))
                except ValueError, e:
                    log.debug(e)
                    h.flash_error(_('Invalid upload URL'))
                except etree.XMLSyntaxError:
                    h.flash_error(_('Invalid XML content'))
                except Exception, e:
                    log.debug(e)
                    log.debug(type(e))
                    h.flash_error(_("Failed to load file"))
                return h.redirect_to(controller='package', action='new') # on error

    def new(self, data=None, errors=None, error_summary=None):
        '''
        Overwrite CKAN method to take uploading xml into sequence.
        '''
        if request.params.get('upload'):
            return self._upload_xml(errors, error_summary)
        else:
            return super(KataPackageController, self).new(data, errors, error_summary)

    def read_rdf(self, id, format):
        '''
        Render dataset in RDF/XML using CKAN's PackageController.read(). Remove unsupported lang attributes created
        by Genshi.
        '''
        return re.sub(r'(<[^<>]*)( lang=\".{2,3}")([^<>]*>)', r'\1\3', self.read(id, format))

    def read_ttl(self, id, format):
        '''
        Render dataset in RDF using turtle format.
        '''
        g = rdflib.Graph().parse(data=self.read_rdf(id, 'rdf'))
        response.headers['Content-Type'] = 'text/turtle'
        return g.serialize(format='turtle')

    def browse(self):
        '''
        List datasets, code is mostly the same as package search.
        '''
        from ckan.lib.search import SearchError
        package_type = 'dataset'

        # default to discipline
        c.facet_choose_title = request.params.get('facet_choose_title') or 'extras_discipline'
        c.facet_choose_item = request.params.get('facet_choose_item')

        try:
            context = {'model': model, 'user': c.user or c.author}
            check_access('site_read', context)
        except NotAuthorized:
            abort(401, _('Not authorized to see this page'))

        q = c.q = u''
        c.query_error = False
        try:
            page = int(request.params.get('page', 1))
        except ValueError, e:
            abort(400, ('"page" parameter must be an integer'))

        limit = 50

        params_nopage = [(k, v) for k, v in request.params.items()
                         if k != 'page']

        def remove_field(key, value=None, replace=None):
            return h.remove_url_param(key, value=value, replace=replace,
                                      controller='ckanext.kata.controllers:KataPackageController', action='browse')

        c.remove_field = remove_field

        sort_by = request.params.get('sort', None)

        params_nosort = [(k, v) for k, v in params_nopage if k != 'sort']

        def _sort_by(fields):
            """
            Sort by the given list of fields.

            Each entry in the list is a 2-tuple: (fieldname, sort_order)

            eg - [('metadata_modified', 'desc'), ('name', 'asc')]

            If fields is empty, then the default ordering is used.
            """
            params = params_nosort[:]

            if fields:
                sort_string = ', '.join('%s %s' % f for f in fields)
                params.append(('sort', sort_string))
            return url_with_params(h.url_for(controller='ckanext.kata.controllers:KataPackageController', action='browse'), params)

        c.sort_by = _sort_by
        if sort_by is None:
            c.sort_by_fields = []
        else:
            c.sort_by_fields = [field.split()[0]
                                for field in sort_by.split(',')]

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            return url_with_params(h.url_for(controller='ckanext.kata.controllers:KataPackageController', action='browse'), params)

        c.search_url_params = urlencode(_encode_params(params_nopage))

        try:
            c.fields = []
            # c.fields_grouped will contain a dict of params containing
            # a list of values eg {'tags':['tag1', 'tag2']}
            c.fields_grouped = {}
            search_extras = {}
            fq = ''

            if c.facet_choose_item:
                # Build query: in dataset browsing the query is limited to a single facet only
                fq = ' %s:"%s"' % (c.facet_choose_title, c.facet_choose_item)
                c.fields.append((c.facet_choose_title, c.facet_choose_item))
                c.fields_grouped[c.facet_choose_title] = [c.facet_choose_item]

            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author, 'for_view': True}

            if not asbool(config.get('ckan.search.show_all_types', 'False')):
                fq += ' +dataset_type:dataset'

            facets = OrderedDict()

            default_facet_titles = {
                    'organization': _('Organizations'),
                    'groups': _('Groups'),
                    'tags': _('Tags'),
                    'res_format': _('Formats'),
                    'license_id': _('License'),
                    }

            for facet in g.facets:
                if facet in default_facet_titles:
                    facets[facet] = default_facet_titles[facet]
                else:
                    facets[facet] = facet

            # Facet titles
            for plugin in p.PluginImplementations(p.IFacets):
                facets = plugin.dataset_facets(facets, package_type)

            c.facet_titles = facets

            data_dict = {
                'q': q,
                'fq': fq.strip(),
                'facet.field': facets.keys(),
                'rows': limit,
                'start': (page - 1) * limit,
                'sort': sort_by,
                'extras': search_extras
            }

            query = get_action('package_search')(context, data_dict)
            c.sort_by_selected = query['sort']

            c.page = h.Page(
                collection=query['results'],
                page=page,
                url=pager_url,
                item_count=query['count'],
                items_per_page=limit
            )
            c.facets = query['facets']
            c.search_facets = query['search_facets']
            c.page.items = query['results']
        except SearchError, se:
            log.error('Dataset search error: %r', se.args)
            c.query_error = True
            c.facets = {}
            c.search_facets = {}
            c.page = h.Page(collection=[])
        c.search_facets_limits = {}
        for facet in c.search_facets.keys():
            limit = 0
            c.search_facets_limits[facet] = limit

        maintain.deprecate_context_item(
          'facets',
          'Use `c.search_facets` instead.')

        return render('kata/browse.html')


class KataInfoController(BaseController):
    '''
    KataInfoController provides info pages, which
    are non-dynamic and visible for all
    '''

    def render_help(self):
        '''
        Provides the help page
        '''
        return render('kata/help.html')

    def render_faq(self):
        '''
        Provides the FAQ page
        '''
        return render('kata/faq.html')

    def render_data_model(self):
        '''
        Provides the data-model as a separate page
        '''

        return render('kata/data-model.html')


class MalwareScanningStorageController(StorageController):
    '''
    MalwareScanningStorageController extends the standard CKAN StorageController
    class by adding an optional malware check on file uploads.

    Malware scanning is disabled by default but can be enabled by setting
    the configuration option kata.storage.malware_scan to true.
    When scanning is enabled, not having a ClamAV daemon running
    will cause uploads to be rejected.
    '''

    def upload_handle(self):
        params = dict(request.params.items())
        field_storage = params.get('file')
        buffer = field_storage.file

        do_scan = config.get('kata.storage.malware_scan', False)

        if not do_scan:
            passed = True
        else:
            try:
                passed = clamd_wrapper.scan_for_malware(buffer)
                # reset the stream so that the data can be properly read again
                buffer.seek(0)
            except clamd_wrapper.MalwareCheckError as err:
                passed = False
                log.error(str(err))

        if passed:
            return StorageController.upload_handle(self)
        else:
            # TODO: produce a meaningful error message through javascript?
            abort(403)

