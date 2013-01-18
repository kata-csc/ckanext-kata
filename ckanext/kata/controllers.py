'''Metadata based controllers for KATA.
'''

from ckan.lib.base import BaseController, c, h
from ckan.controllers.api import ApiController
from ckan.model import Package, User, Related, Member, Group
import ckan.model.misc as misc
import ckan.model as model

from pylons import response, config, request
from pylons.decorators.cache import beaker_cache
from rdflib.term import Identifier, Statement, Node, Variable
from rdflib.namespace import ClosedNamespace
from vocab import Graph, URIRef, Literal, BNode
from vocab import DC, DCES, DCAT, FOAF, OWL, RDF, RDFS, UUID, VOID, OPMV, SKOS,\
                    REV, SCOVO, XSD, LICENSES

import logging
from genshi.template._ast24 import Pass
from urnhelper import URNHelper

log = logging.getLogger('ckanext.kata.controller')


def get_extra_contact(context, data_dict, key="contact_name"):
    model = context['model']

    terms = data_dict.get('query') or data_dict.get('q') or []
    if isinstance(terms, basestring):
        terms = [terms]
    terms = [t.strip() for t in terms if t.strip()]

    if 'fields' in data_dict:
        log.warning('"fields" parameter is deprecated.  '
                    'Use the "query" parameter instead')

    offset = data_dict.get('offset')
    limit = data_dict.get('limit')

    # TODO: should we check for user authentication first?
    q = model.Session.query(model.PackageExtra)

    if not len(terms):
        return [], 0

    for term in terms:
        escaped_term = misc.escape_sql_like_special_characters(term, escape='\\')
        q = q.filter(model.PackageExtra.key.contains(key))
        q = q.filter(model.PackageExtra.value.ilike("%" + escaped_term + "%"))

    q = q.offset(offset)
    q = q.limit(limit)
    return q.all()

def get_discipline(context, data_dict):
    model = context['model']

    terms = data_dict.get('query') or data_dict.get('q') or []
    if isinstance(terms, basestring):
        terms = [terms]
    terms = [t.strip() for t in terms if t.strip()]

    if 'fields' in data_dict:
        log.warning('"fields" parameter is deprecated.  '
                    'Use the "query" parameter instead')

    offset = data_dict.get('offset')
    limit = data_dict.get('limit')

    # TODO: should we check for user authentication first?
    q = model.Session.query(model.Group)

    if not len(terms):
        return [], 0
    katagrp = Group.get('KATA')
    for term in terms:
        escaped_term = misc.escape_sql_like_special_characters(term, escape='\\')
        q = q.filter(model.Member.group_id == katagrp.id)
        q = q.filter(model.Group.name.ilike("%" + escaped_term + "%"))
    q = q.offset(offset)
    q = q.limit(limit)
    return q.all()


class MetadataController(BaseController):

    def _make_rights_element(self, extras):
        xmlstr = ""
        if extras["access"] == 'contact':
            xmlstr = '<RightsDeclaration RIGHTSCATEGORY="COPYRIGHTED">' + extras['accessrequestURL'] + '</RightsDeclaration>'
        if extras["access"] in ('ident', 'free'):
            xmlstr = '<RightsDeclaration RIGHTSCATEGORY="LICENSED">' + extras['licenseURL'] + '</RightsDeclaration>'
        if extras["access"] == 'form':
            xmlstr = '<RightsDeclaration RIGHTSCATEGORY="CONTRACTUAL">' + extras['accessRights'] + '</RightsDeclaration>'
        return Literal(xmlstr, datatype=RDF.XMLLiteral)

    def _make_temporal(self, extras):
        dcmi_period = ""
        if all(k in extras for k in ("temporal_coverage_begin",
                                    "temporal_coverage_end")):
            dcmi_period = "start=%s; end=%s; scheme=ISO-8601;" % (extras["temporal_coverage_begin"],
                                                            extras["temporal_coverage_end"])
        return dcmi_period

    @beaker_cache(type="dbm", expire=604800)
    def urnexport(self):
        response.headers['Content-type'] = 'text/xml'
        return URNHelper.list_packages()

    def tordf(self, id, format):
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
                profileurl = URIRef(config.get('ckan.site_url', '') +\
                    h.url_for(controller="user", action="read", id=user.name))
            graph.add((metadoc, DC.identifier, Literal(data["id"])\
                                if 'identifier' not in data["extras"]\
                                else URIRef(data["extras"]["identifier"])))
            graph.add((metadoc, DC.modified, Literal(data["metadata_modified"],
                                                 datatype=XSD.dateTime)))
            graph.add((metadoc, FOAF.primaryTopic, Identifier(data['name'])))
            uri = URIRef(data['name'])
            if data["license"]:
                graph.add((uri, DC.rights, Literal(data["license"])))
            if "versionPID" in data["extras"]:
                graph.add((uri, DC.identifier, Literal(data["extras"]["versionPID"])))
            graph.add((uri, DC.identifier, Literal(data["name"])))
            graph.add((uri, DC.modified, Literal(data.get("version", ''),
                                                 datatype=XSD.dateTime)))
            org = URIRef(FOAF.Person)
            if profileurl:
                graph.add((uri, DC.publisher, profileurl))
                graph.add((profileurl, RDF.type, org))
                graph.add((profileurl, FOAF.name, Literal(data["extras"]["publisher"])))
                graph.add((profileurl, FOAF.phone, Identifier(data["extras"]["phone"])))
                graph.add((profileurl, FOAF.homepage, Identifier(data["extras"]["contactURL"])))
                graph.add((uri, DC.rightsHolder, URIRef(data["extras"]["owner"])
                                                if data["extras"]["owner"].startswith(('http','urn'))\
                                                else Literal(data["extras"]["owner"])))
            log.debug(data["extras"])
            if all((k in data["extras"] and data["extras"][k] != "") for k in ("project_name",\
                                                 "project_homepage",\
                                                 "project_funding",\
                                                 "funder")):
                project = URIRef(FOAF.Project)
                projecturl = URIRef(data["extras"]["project_homepage"])
                graph.add((uri, DC.contributor, projecturl))
                graph.add((projecturl, RDF.type, project))
                graph.add((projecturl, FOAF.name, Literal(data["extras"]["project_name"])))
                graph.add((projecturl, FOAF.homepage, Identifier(data["extras"]["project_homepage"])))
                graph.add((projecturl, RDFS.comment,
                            Literal(data["extras"]["project_funder"])))
            for key in data["extras"]:
                log.debug(key)
                if key.startswith('author'):
                    graph.add((uri, DC.creator, URIRef(data["extras"][key])\
                                                if data["extras"][key].startswith(('http','urn'))\
                                                else Literal(data["extras"][key])))
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
            if "access" in data["extras"]:
                graph.add((uri, DC.rights, self._make_rights_element(data["extras"])))

            # Extended metadatamodel

            if all(k in data["extras"] for k in ("temporal_coverage_begin",
                                                  "temporal_coverage_end")):
                graph.add((uri, DC.temporal, Literal(self._make_temporal(data["extras"]))))
            if "geographical_coverage" in data["extras"]:
                graph.add((uri, DC.spatial, Literal(data["extras"]["geographical_coverage"])))
            for rel in Related.get_for_dataset(pkg):
                graph.add((uri, DC.isReferencedBy, Literal(rel.related.title)))
            if "notes_rendered" in data:
                graph.add((uri, DC.description, Literal(data["notes_rendered"])))

            response.headers['Content-type'] = 'text/xml'
            if format == 'rdf':
                format = 'pretty-xml'
            return graph.serialize(format=format)
        else:
            return ""


class KATAApiController(ApiController):

    def author_autocomplete(self):
        pass

    def organization_autocomplete(self):
        pass

    def contact_autocomplete(self):
        q = request.params.get('incomplete', '')
        limit = request.params.get('limit', 10)
        tag_names = []
        if q:
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author}

            data_dict = {'q': q, 'limit': limit}

            tag_names = get_extra_contact(context, data_dict)

        tag_names = [k.value for k in tag_names]
        resultSet = {
            'ResultSet': {
                'Result': [{'Name': tag} for tag in tag_names]
            }
        }
        return self._finish_ok(resultSet)

    def discipline_autocomplete(self):
        q = request.params.get('incomplete', '')
        limit = request.params.get('limit', 10)
        tag_names = []
        if q:
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author}

            data_dict = {'q': q, 'limit': limit}

            tag_names = get_discipline(context, data_dict)

        tag_names = [k.name for k in tag_names]
        resultSet = {
            'ResultSet': {
                'Result': [{'Name': tag} for tag in tag_names]
            }
        }
        return self._finish_ok(resultSet)

    def owner_autocomplete(self):
        q = request.params.get('incomplete', '')
        limit = request.params.get('limit', 10)
        tag_names = []
        if q:
            context = {'model': model, 'session': model.Session,
                       'user': c.user or c.author}

            data_dict = {'q': q, 'limit': limit}

            tag_names = get_extra_contact(context, data_dict, key="owner_name")

        tag_names = [k.value for k in tag_names]
        resultSet = {
            'ResultSet': {
                'Result': [{'Name': tag} for tag in tag_names]
            }
        }
        return self._finish_ok(resultSet)
