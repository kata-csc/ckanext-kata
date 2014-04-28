# coding=utf8
"""
Controllers for Kata.
"""

import json
import logging
import functionally as fn
from rdflib.namespace import XSD
from rdflib.term import Identifier, URIRef, Literal, BNode
import urllib2

from paste.deploy.converters import asbool
from pylons import response, config, request, session, g
from pylons.decorators.cache import beaker_cache
from pylons.i18n import _

from ckan.controllers.api import ApiController
from ckan.controllers.package import PackageController
from ckan.controllers.user import UserController
import ckan.lib.i18n
from ckan.lib.base import BaseController, c, h, redirect, render
from ckan.lib.email_notifications import send_notification
from ckan.logic import get_action
import ckan.model as model
from ckan.model import Package, User, Related, meta, license
from ckan.model.authz import add_user_to_role
from ckanext.kata.model import KataAccessRequest
from ckanext.kata.urnhelper import URNHelper
from ckanext.kata.vocab import DC, FOAF, RDF, RDFS, Graph

log = logging.getLogger('ckanext.kata.controller')

# BUCKET = config.get('ckan.storage.bucket', 'default')


def get_package_owner(package):
    """Returns the user id of the package admin for the specified package.
       If multiple user accounts are associated with the package as admins,
       an arbitrary one is returned.
    """
    userid = None
    for role in package.roles:
        if role.role == "admin":
            userid = role.user_id
            break
    return userid


class MetadataController(BaseController):
    '''
    RDF export.

    TODO: Would be simpler to just overwrite CKAN's read.rdf.
    '''

    def _make_rights_element(self, extras):
        '''
        Return license information as an RDF literal.

        :param extras:
        :return:
        '''

        xmlstr = ""
        
        if extras["availability"] == 'contact_owner':
            xmlstr = '<RightsDeclaration RIGHTSCATEGORY="COPYRIGHTED">'
            if extras.get('license_URL'):
                xmlstr += extras['license_URL']
            xmlstr += '</RightsDeclaration>'
        if extras["availability"] in ('direct_download', 'access_request'):
            xmlstr = '<RightsDeclaration RIGHTSCATEGORY="LICENSED">'
            if extras.get('license_URL'):
                xmlstr += extras['license_URL']
            xmlstr += '</RightsDeclaration>'
        if extras["availability"] == 'access_application':
            xmlstr = '<RightsDeclaration RIGHTSCATEGORY="CONTRACTUAL">' + extras[
                'access_application_URL'] + '</RightsDeclaration>'
        if extras["availability"] == 'through_provider':
            xmlstr = '<RightsDeclaration RIGHTSCATEGORY="LICENSED">' + extras[
                'through_provider_URL'] + ' '
            if extras.get('license_URL'):
                xmlstr += extras['license_URL']
            xmlstr += '</RightsDeclaration>'

        return Literal(xmlstr, datatype=RDF.XMLLiteral)

    def _make_temporal(self, extras):
        dcmi_period = ""
        if all(k in extras for k in ("temporal_coverage_begin",
                                     "temporal_coverage_end")):
            dcmi_period = "start=%s; end=%s; scheme=ISO-8601;" % (extras["temporal_coverage_begin"],
                                                                  extras["temporal_coverage_end"])
        return dcmi_period

    @beaker_cache(type="dbm", expire=86400)
    def urnexport(self):
        response.headers['Content-type'] = 'text/xml'
        return URNHelper.list_packages()

    def tordf(self, id, format):
        '''
        Get an RDF presentation of a package.

        :param id:
        :param format:
        :return:
        '''
        graph = Graph()
        pkg = Package.get(id)
        if pkg:
            data = pkg.as_dict()
            metadoc = URIRef('')
            user = None
            if pkg.roles:
                owner = [role for role in pkg.roles if role.role == 'admin']
                if len(owner):
                    user = User.get(owner[0].user_id)
            profileurl = ""
            if user:
                profileurl = URIRef(config.get('ckan.site_url', '') + \
                                    h.url_for(controller="user", action="read", id=user.name))
            graph.add((metadoc, DC.identifier, Literal(data["id"]) \
                if 'identifier' not in data["extras"] \
                else URIRef(data["extras"]["identifier"])))
            if data["metadata_modified"]:
                graph.add((metadoc, DC.modified, Literal(data["metadata_modified"], datatype=XSD.dateTime)))
            graph.add((metadoc, FOAF.primaryTopic, Identifier(data['name'])))
            uri = URIRef(data['name'])
            if data["license"]:
                graph.add((uri, DC.rights, Literal(data["license"])))

            licenseRegister = license.LicenseRegister()
            # harvested data fails without the declaration and try-except
            license_url = ''
            try:
                license_url = licenseRegister.get(data["license_id"]).url
            except:
                log.debug('licenseRegister had no url')
            if license_url:
                graph.add((uri, DC.license, URIRef(license_url)))

            if "version_PID" in data["extras"]:
                graph.add((uri, DC.identifier, Literal(data["extras"]["version_PID"])))

            graph.add((uri, DC.identifier, Literal(data["name"])))

            if data["version"]:
                graph.add((uri, DC.modified, Literal(data["version"], datatype=XSD.dateTime)))

            org = URIRef(FOAF.Person)
            if profileurl:
                graph.add((uri, DC.publisher, profileurl))
                graph.add((profileurl, RDF.type, org))
                if "maintainer" in data["extras"]:
                    graph.add((profileurl, FOAF.name, Literal(data["maintainer"])))
                if "contact_phone" in data["extras"]:
                    graph.add((profileurl, FOAF.phone, Identifier(data["extras"]["contact_phone"])))
                if "contact_URL" in data["extras"]:
                    graph.add((profileurl, FOAF.homepage, Identifier(data["extras"]["contact_URL"])))
                if "owner" in data["extras"]:
                    graph.add((uri, DC.rightsHolder, URIRef(data["extras"]["owner"])
                    if data["extras"]["owner"].startswith(('http', 'urn')) \
                        else Literal(data["extras"]["owner"])))
            log.debug(data["extras"])
            if all((k in data["extras"] and data["extras"][k] != "") for k in ("project_name", \
                                                                               "project_homepage", \
                                                                               "project_funding", \
                                                                               "project_funder")):
                project = URIRef(FOAF.Project)
                projecturl = URIRef(data["extras"]["project_homepage"])
                graph.add((uri, DC.contributor, projecturl))
                graph.add((projecturl, RDF.type, project))
                graph.add((projecturl, FOAF.name, Literal(data["extras"]["project_name"])))
                graph.add((projecturl, FOAF.homepage, Identifier(data["extras"]["project_homepage"])))
                graph.add((projecturl, RDFS.comment,
                           Literal(" ".join((data["extras"]["project_funder"],
                                             data["extras"]["project_funding"])))))
            for key in data["extras"]:
                log.debug(key)
                # TODO: Fix authors to new format
                if key.startswith('author'):
                    graph.add((uri, DC.creator, URIRef(data["extras"][key]) \
                        if data["extras"][key].startswith(('http', 'urn')) \
                        else Literal(data["extras"][key])))

                # TODO: Fix titles to new format
                if key.startswith("title"):
                    lastlangnum = key.split('_')[-1]
                    log.debug(lastlangnum)
                    lastlang = data["extras"]["lang_title_%s" % lastlangnum]
                    graph.add((uri, DC.title, Literal(data["extras"][key],
                                                      lang=lastlang)))
            for tag in data['tags']:
                graph.add((uri, DC.subject, Literal(tag)))
            for lang in data["extras"].get("language", "").split(','):
                graph.add((uri, DC.language, Literal(lang.strip())))
            if "availability" in data["extras"]:
                graph.add((uri, DC.rights, self._make_rights_element(data["extras"])))

            # Extended metadatamodel

            if all(k in data["extras"] for k in ("temporal_coverage_begin", "temporal_coverage_end")) \
                and data["extras"]["temporal_coverage_begin"] and data["extras"]["temporal_coverage_end"]:
                graph.add((uri, DC.temporal, Literal(self._make_temporal(data["extras"]))))
            if "geographical_coverage" in data["extras"]:
                graph.add((uri, DC.spatial, Literal(data["extras"]["geographical_coverage"])))
            for rel in Related.get_for_dataset(pkg):
                graph.add((uri, DC.isReferencedBy, Literal(rel.related.title)))
            if "notes" in data:
                graph.add((uri, DC.description, Literal(data["notes"])))

            # TODO: Add agents

            # for agent in data.get('agent', []):
            #
            #     # agent_ref = URIRef(agent['URL']) \
            #     #     if agent.get('URL') \
            #     #     else BNode()
            #     agent_ref = BNode()
            #
            #     if agent.get('name'):
            #         graph.add((agent_ref, FOAF.name, agent.get('name')))
            #     if agent.get('URL'):
            #         graph.add((agent_ref, FOAF.homepage, agent.get('URL')))
            #
            #     graph.add((uri, DC.creator, agent_ref))

            response.headers['Content-type'] = 'text/xml'
            if format == 'rdf':
                format = 'pretty-xml'
            return graph.serialize(format=format)
        else:
            return ""


class KATAApiController(ApiController):
    '''
    Functions for autocomplete fields in add dataset form
    '''

    def tag_autocomplete(self):
        query = request.params.get('incomplete', '')
        return self._onki_autocomplete(query, "yso")

    def discipline_autocomplete(self):
        query = request.params.get('incomplete', '')
        return self._onki_autocomplete(query, "okm-tieteenala")

    def location_autocomplete(self):
        query = request.params.get('incomplete', '')
        return self._onki_autocomplete(query, "paikat")

    def _onki_autocomplete(self, query, vocab):
        url_template = "http://dev.finto.fi/rest/v1/search?query={q}*&vocab={v}"

        labels = []
        if query:
            url = url_template.format(q=query, v=vocab)
            data = urllib2.urlopen(url).read()
            jsondata = json.loads(data)
            if u'results' in jsondata:
                results = jsondata['results']
                labels = [concept['prefLabel'].encode('utf-8') for concept in results]

        result_set = {
            'ResultSet': {
                'Result': [{'Name': label} for label in labels]
            }
        }
        return self._finish_ok(result_set)


class AccessRequestController(BaseController):
    '''
    AccessRequestController class provides a feature to ask
    for editor rights to a dataset. On the other hand,
    it also provides the process to grant them upon request.
    '''

    def _have_pending_requests(self, pkg_id, user_id):
        """
        Returns whether there are already pending requests
        from the given user regarding the given package.
        """

        pending_requests = model.Session.query(KataAccessRequest).filter(
            KataAccessRequest.pkg_id == pkg_id, KataAccessRequest.user_id == user_id)
        return pending_requests.count() > 0

    def create_request(self, pkg_id):
        """
        Creates a new editor access request in the database.
        """

        url = h.url_for(controller='package', action='read', id=pkg_id)

        pkg = Package.get(pkg_id)
        pkg_title = pkg.title if pkg.title else pkg.name

        user = c.userobj if c.userobj else None
        if user:
            if not self._have_pending_requests(pkg_id, user.id):
                req = KataAccessRequest(user.id, pkg.id)
                req.save()
                h.flash_success(_("You now requested editor rights to package %s" % pkg_title))
                redirect(url)
            else:
                h.flash_error(_("A request is already pending"))
                redirect(url)
        else:
            h.flash_error(_("You must be logged in to request edit access"))
            redirect(url)

    def unlock_access(self, id):
        q = model.Session.query(KataAccessRequest)
        q = q.filter_by(id=id)
        req = q.first()
        if req:
            user = User.get(req.user_id)
            pkg = Package.get(req.pkg_id)
            pkg_title = pkg.title if pkg.title else pkg.name
            add_user_to_role(user, 'editor', pkg)
            url = h.url_for(controller='package', action='read', id=req.pkg_id)
            h.flash_success(_("%s now has editor rights to package %s" % (user.name, pkg_title)))
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


'''DataMiningController is here for reference, some stuff like the file parsing might be useful'''
# class DataMiningController(BaseController):
#     '''
#     Controller for scraping metadata content from files.
#     '''
#
#     def read_data(self, id, resource_id):
#         """
#         Scrape all words from a file and save it to extras.
#         """
#         res = Resource.get(resource_id)
#         pkg = Package.get(id)
#         c.pkg_dict = pkg.as_dict()
#         c.package = pkg
#         c.resource = get_action('resource_show')({'model': model},
#                                                      {'id': resource_id})
#         label = res.url.split(config.get('ckan.site_url') + '/storage/f/')[-1]
#         label = urllib2.unquote(label)
#         ofs = get_ofs()
#
#         try:
#             # Get file location
#             furl = ofs.get_url(BUCKET, label).split('file://')[-1]
#         except FileNotFoundException:
#             h.flash_error(_('Cannot do data mining on remote resource!'))
#             url = h.url_for(controller='package', action='resource_read',
#                             id=id, resource_id=resource_id)
#             return redirect(url)
#
#         wordstats = {}
#         ret = {}
#
#         if res.format in ('TXT', 'txt'):
#             wdsf, wdspath = tempfile.mkstemp()
#             os.write(wdsf, "%s\nmetadata description title information" % furl)
#
#             with os.fdopen(wdsf, 'r') as wordfile:
#                 preproc = orngText.Preprocess()
#                 table = orngText.loadFromListWithCategories(wdspath)
#                 data = orngText.bagOfWords(table, preprocessor=preproc)
#                 words = orngText.extractWordNGram(data, threshold=10.0, measure='MI')
#
#             for i in range(len(words)):
#                 d = words[i]
#                 wordstats = d.get_metas(str)
#
#             for k, v in wordstats.items():
#                 if v.value > 10.0:
#                     ret[unicode(k, 'utf8')] = v.value
#
#             c.data_tags = sorted(ret.iteritems(), key=itemgetter(1), reverse=True)[:30]
#             os.remove(wdspath)
#
#             for i in range(len(data)):
#                     d = words[i]
#                     wordstats = d.get_metas(str)
#
#             words = []
#             for k, v in wordstats.items():
#                 words.append(k)
#
#             # Save scraped words to extras.
#
#             model.repo.new_revision()
#             if not 'autoextracted_description' in pkg.extras:
#                 pkg.extras['autoextracted_description'] = ' '.join(words)
#
#             pkg.save()
#
#             return render('datamining/read.html')
#
#         elif res.format in ('odt', 'doc', 'xls', 'ods', 'odp', 'ppt', 'doc', 'html'):
#
#             textfd, textpath = convert_to_text(res, furl)
#
#             if not textpath:
#                 h.flash_error(_('This file could not be mined for any data!'))
#                 os.close(textfd)
#                 return render('datamining/read.html')
#             else:
#                 wdsf, wdspath = tempfile.mkstemp()
#                 os.write(wdsf, "%s\nmetadata description title information" % textpath)
#                 preproc = orngText.Preprocess()
#                 table = orngText.loadFromListWithCategories(wdspath)
#                 data = orngText.bagOfWords(table, preprocessor=preproc)
#                 words = orngText.extractWordNGram(data, threshold=10.0, measure='MI')
#
#                 for i in range(len(words)):
#                     d = words[i]
#                     wordstats = d.get_metas(str)
#
#                 for k, v in wordstats.items():
#                     if v.value > 10.0:
#                         ret[unicode(k, 'utf8')] = v.value
#
#                 c.data_tags = sorted(ret.iteritems(), key=itemgetter(1), reverse=True)[:30]
#                 os.close(textfd)
#                 os.close(wdsf)
#                 os.remove(wdspath)
#                 os.remove(textpath)
#
#                 for i in range(len(data)):
#                     d = words[i]
#                     wordstats = d.get_metas(str)
#
#                 words = []
#
#                 for k, v in wordstats.items():
#                     log.debug(k)
#                     words.append(substitute_ascii_equivalents(k))
#
#                 model.repo.new_revision()
#
#                 if not 'autoextracted_description' in pkg.extras:
#                     pkg.extras['autoextracted_description'] = ' '.join(words)
#
#                 pkg.save()
#
#                 return render('datamining/read.html')
#         else:
#             h.flash_error(_('This metadata document is not in proper format for data mining!'))
#             url = h.url_for(controller='package', action='resource_read',
#                             id=id, resource_id=resource_id)
#             return redirect(url)
#
#     def save(self):
#         if not c.user:
#             return
#
#         model.repo.new_revision()
#         data = clean_dict(unflatten(tuplize_dict(parse_params(request.params))))
#         package = Package.get(data['pkgid'])
#         keywords = []
#         context = {'model': model, 'session': model.Session,
#                    'user': c.user}
#
#         if check_access('package_update', context, data_dict={"id": data['pkgid']}):
#
#             for k, v in data.items():
#                 if k.startswith('kw'):
#                     keywords.append(v)
#
#             tags = package.get_tags()
#
#             for kw in keywords:
#                 if not kw in tags:
#                     package.add_tag_by_name(kw)
#
#             package.save()
#             url = h.url_for(controller='package', action='read', id=data['pkgid'])
#             redirect(url)
#         else:
#             redirect('/')


class ContactController(BaseController):
    """
    Add features to contact the dataset's owner. 
    
    From the web page, this can be seen from the link telling that this dataset is accessible by contacting the author. 
    The feature provides a form for message sending, and the message is sent via e-mail. 
    """

    def _send_message(self, recipient, email, email_dict):
        ''' Send message to given email '''
        import ckan.lib.mailer

        try:
            ckan.lib.mailer.mail_recipient(recipient, email,
                                           email_dict['subject'], email_dict['body'])
        except ckan.lib.mailer.MailerException:
            raise

    def _send_if_allowed(self, pkg_id, subject, msg, prologue=None, epilogue=None, recipient=None, email=None):
        """
        Send a contact e-mail if allowed.

        All of the arguments should be unicode strings.
        """

        package = Package.get(pkg_id)

        prologue = prologue + "\n\n\n" if prologue else ""
        epilogue = "\n\n\n" + epilogue if epilogue else ""

        full_msg = u"{a}{b}{c}".format(a=prologue, b=msg, c=epilogue)
        email_dict = {"subject": subject,
                      "body": full_msg}

        if c.user:
            owner_id = get_package_owner(package)
            if owner_id:
                owner = User.get(owner_id)
                owner_dict = owner.as_dict()
                owner_dict['name'] = owner.fullname if owner.fullname else owner.name
                if msg:
                    model.repo.new_revision()
                    if recipient == None:
                        send_notification(owner_dict, email_dict)
                    else:
                        self._send_message(recipient, email, email_dict)
                    self._mark_owner_as_contacted(c.userobj, pkg_id)
                    h.flash_notice(_("Message sent"))
                else:
                    h.flash_error(_("No message"))
            else:
                h.flash_error(_("No owner found"))
        else:
            h.flash_error(_("Please login"))

    def _mark_owner_as_contacted(self, userobj, pkg_id):
        """Mark this user as having already contacted the package owner"""

        if "contacted" not in userobj.extras:
            userobj.extras['contacted'] = []

        userobj.extras['contacted'].append(pkg_id)
        userobj.save()

    def send_contact(self, pkg_id):
        '''
        Send a user message from CKAN to dataset distributor contact. Not used.
        '''

        prologue_template = u'{a} ({b}) has sent you a message regarding the following dataset:\
\n\n{c} (Identifier: {d})\n\nThe message is below.\n\n{a} ({b}) on lähettänyt sinulle viestin koskien tietoaineistoa:\
\n\n{c} (Tunniste: {d})\n\nViesti:\n\n    ---'

        epilogue = u'    ---\
\n\nPlease do not reply directly to this e-mail.\
\nIf you need to reply to the sender, use the direct e-mail address above.\
\n\nÄlä vastaa suoraan tähän viestiin. Jos vastaat lähettäjälle, \
käytä yllä olevaa sähköpostiosoitetta.'

        package = Package.get(pkg_id)
        package_title = package.title if package.title else package.name
        if c.userobj:
            user_name = c.userobj.fullname if c.userobj.fullname else c.userobj.name
            # email = package.maintainer_email
            email_tuples = filter(lambda (k, v): k.startswith('contact_') and k.endswith('_email'), package.extras.iteritems())
            emails = [con[1] for con in email_tuples]
            email = fn.first(emails)
            recipient = package.maintainer

            user_msg = request.params.get('msg', '')
            prologue = prologue_template.format(a=user_name, b=c.userobj.email, c=package_title, d=package.name)

            subject = "Message regarding dataset / Viesti koskien tietoaineistoa %s" % package_title
            self._send_if_allowed(pkg_id, subject, user_msg, prologue, epilogue, recipient, email)
        else:
            h.flash_error(_("Please login"))

        url = h.url_for(controller='package',
                        action="read",
                        id=package.id)

        return redirect(url)

    def send_request(self, pkg_id):
        '''
        Send a request to access data to CKAN dataset owner.
        '''

        prologue_template = u'{a} ({b}) is requesting access to data in dataset\n\n{c} (Identifier: {d})\n\n\
for which you are currently marked as distributor.\n\nThe message is below.\n\n\
{a} ({b}) pyytää dataa, joka liittyy tietoaineistoon\n\n{c} (Tunniste: {d})\n\nja johon sinut on merkitty jakelijaksi. \
Mukaan liitetty viesti on alla.\n\n    ---'

        epilogue = u'    ---\n\nPlease do not reply directly to this e-mail.\n\
If you need to reply to the sender, use the direct e-mail address above.\n\n\
Älä vastaa suoraan tähän viestiin. Jos haluat lähettää viestin \
lähettäjälle, käytä yllä olevaa sähköpostiosoitetta.'

        package = Package.get(pkg_id)
        package_title = package.title if package.title else package.name
        if c.userobj:
            user_name = c.userobj.fullname if c.userobj.fullname else c.userobj.name

            user_msg = request.params.get('msg', '')
            prologue = prologue_template.format(a=user_name, b=c.userobj.email, c=package_title, d=package.name)

            subject = _("Data access request for dataset / Datapyynto tietoaineistolle %s" % package_title)
            self._send_if_allowed(pkg_id, subject, user_msg, prologue, epilogue)
        else:
            h.flash_error(_("Please login"))

        url = h.url_for(controller='package',
                        action="read",
                        id=package.id)

        return redirect(url)


    def render_contact(self, pkg_id):
        """
        Render the contact form if allowed.
        """

        c.package = Package.get(pkg_id)
        url = h.url_for(controller='package',
                        action="read",
                        id=c.package.id)
        if c.user:
            if pkg_id not in c.userobj.extras.get('contacted', []):
                return render('contact/contact_form.html')
            else:
                h.flash_error(_("Already contacted"))
                return redirect(url)
        else:
            h.flash_error(_("Please login"))
            return redirect(url)

    def render_request(self, pkg_id):
        """
        Render the access request contact form if allowed.
        """

        c.package = Package.get(pkg_id)
        url = h.url_for(controller='package',
                        action="read",
                        id=c.package.id)
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
        """
        Minor rewrite to redirect the user to the own profile page instead of
        the dashboard.
        @return - some sort of redirect object??
        """
        # we need to set the language via a redirect
        lang = session.pop('lang', None)
        session.save()
        came_from = request.params.get('came_from', '')

        # we need to set the language explicitly here or the flash
        # messages will not be translated.
        ckan.lib.i18n.set_lang(lang)

        if c.user:
            context = {'model': model,
                       'user': c.user}

            data_dict = {'id': c.user}

            user_dict = get_action('user_show')(context, data_dict)

            h.flash_success(_("%s is now logged in") %
                            user_dict['display_name'])
            if came_from:
                return h.redirect_to(str(came_from))
                # Rewritten in ckanext-kata
            return h.redirect_to(controller='user', action='read', id=c.userobj.name)
        else:
            err = _('Login failed. Bad username or password.')
            if g.openid_enabled:
                err += _(' (Or if using OpenID, it hasn\'t been associated '
                         'with a user account.)')
            if asbool(config.get('ckan.legacy_templates', 'false')):
                h.flash_error(err)
                h.redirect_to(locale=lang, controller='user',
                              action='login', came_from=came_from)
            else:
                return self.login(error=err)


class KataPackageController(PackageController):
    """
    Adds advanced search feature.
    """

    def advanced_search(self):
        """
        Parse query parameters from different search form inputs, modify into
        one query string 'q' in the context and call basic search() method of
        the super class.

        @return - dictionary with keys results and count
        """
        # parse author search into q
        q_author = c.q_author = request.params.get('q_author', u'')

        # unicode format (decoded from utf8)
        q_free = c.q_free = request.params.get('q_free', u'')
        q = c.q = q_free + u' AND ' + u'author:' + q_author

        log.debug('advanced_search(): request.params.items(): %r' % request.params.items())
        #log.debug('advanced_search(): q: %r' % q)
        log.debug('advanced_search(): call to search()')
        return self.search()


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

