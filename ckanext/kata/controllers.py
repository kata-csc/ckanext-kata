'''Metadata based controllers for KATA.
'''

from ckan.lib.base import BaseController, c, h
from ckan.controllers.api import ApiController
from ckan.model import Package, Vocabulary, Session
import ckan.model.misc as misc
import ckan.model as model

from pylons import response, config, request

from rdflib.term import Identifier, Statement, Node, Variable
from rdflib.namespace import ClosedNamespace
from vocab import Graph, URIRef, Literal, BNode
from vocab import DC, DCES, DCAT, FOAF, OWL, RDF, RDFS, UUID, VOID, OPMV, SKOS,\
                    REV, SCOVO, XSD, LICENSES

import logging
from genshi.template._ast24 import Pass

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


class MetadataController(BaseController):

    def _check_and_gather_role(self, extra):
        if extra.startswith('role_'):
            for role in config.get('kata.contact_roles', []).split(', '):
                if extra.endswith(role):
                    if role in self.roles:
                        self.roles[role].append(extra)
                    else:
                        self.roles[role] = []
                        self.roles[role].append(extra)

    def tordf(self, id, format):
        graph = Graph()
        pkg = Package.get(id)
        if pkg:
            data = pkg.as_dict()
            uri = URIRef(config.get('ckan.site_url', '') + h.url_for(controller='package', action='read',
                                   id=id))
            graph.add((uri, DC.identifier, Literal(data["name"])\
                                if 'identifier' not in data["extras"]\
                                else URIRef(data["extras"]["identifier"])))
            graph.add((uri, DC.modified, Literal(pkg.latest_related_revision.timestamp.isoformat(),
                                                 datatype=XSD.date)))
            graph.add((uri, DC.title, Literal(data["title"])))
            if data["license"]:
                graph.add((uri, DC.rights, Literal(data["license"])))
            publisher = BNode()
            graph.add((uri, DC.publisher, publisher))
            graph.add((publisher, FOAF.name, Literal(data["maintainer"])))
            if data["maintainer_email"]:
                graph.add((publisher, FOAF.mbox, Literal(data["maintainer_email"])))
            creator = BNode()
            graph.add((uri, DC.creator, creator))
            graph.add((creator, FOAF.name, Literal(data["author"])))
            if data["author_email"]:
                graph.add((creator, FOAF.mbox, Literal(data["author_email"])))
            self.roles = {}
            for extra in data["extras"]:
                self._check_and_gather_role(extra)
            for key, value in self.roles.iteritems():
                if key in ('Author', 'Producer', 'Publisher'):
                    if key == 'Author':
                        for val in value:
                            creator = BNode()
                            graph.add((uri, DC.creator, creator))
                            graph.add((creator, FOAF.name, Literal(data["extras"][val])))
                    if key == 'Producer':
                        for val in value:
                            contributor = BNode()
                            graph.add((uri, DC.contributor, contributor))
                            graph.add((contributor, FOAF.name, Literal(data["extras"][val])))
                    if key == 'Publisher':
                        for val in value:
                            publisher = BNode()
                            graph.add((uri, DC.publisher, publisher))
                            graph.add((publisher, FOAF.name, Literal(data["extras"][val])))
            for vocab in Session.query(Vocabulary).all():
                for tag in pkg.get_tags(vocab=vocab):
                    tag_id = Identifier(vocab.name + '#' + tag.name)
                    graph.add((uri, DC.subject, tag_id))
                    graph.add((tag_id, RDFS.label, Literal(tag.name)))
            for tag in pkg.get_tags():
                tag_id = BNode()
                graph.add((uri, DC.subject, tag_id))
                graph.add((tag_id, RDFS.label, Literal(tag.name)))
            graph.add((uri, DC.description, Literal(data["notes"])))
            if data["url"]:
                graph.add((uri, DC.source, URIRef(data["url"])))
            for res in data["resources"]:
                url = config.get('ckan.site_url', '') + h.url_for(controller='package',
                                             action='resource_read',
                                             id=data['id'],
                                             resource_id=res['id'])
                extra = Identifier(url)
                graph.add((uri, DC.relation, extra))
                if res["url"]:
                    resurl = res["url"] if res['url'].startswith('http') else\
                             config.get('ckan.site_url', '') + res['url']
                    resurl = URIRef(resurl)
                    graph.add((extra, DC.isPartOf, resurl))
                    if res["size"]:
                        extent = BNode()
                        graph.add((resurl, DC.extent, extent))
                        graph.add((extent, RDF.value, Literal(res['size'])))
                    if res["format"]:
                        isformat = BNode()
                        graph.add((resurl, DC.hasFormat, isformat))
                        hformat = BNode()
                        graph.add((isformat, DC.isFormatOf, hformat))
                        graph.add((hformat, RDFS.label, Literal(res['format'])))
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
