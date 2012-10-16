'''Metadata based controllers for KATA.
'''

from ckan.lib.base import BaseController, c, h
from ckan.model import Package, Vocabulary, Session

from pylons import response, config

from rdflib.term import Identifier, Statement, Node, Variable
from rdflib.namespace import ClosedNamespace
from vocab import Graph, URIRef, Literal, BNode
from vocab import DC, DCES, DCAT, FOAF, OWL, RDF, RDFS, UUID, VOID, OPMV, SKOS,\
                    REV, SCOVO, XSD, LICENSES

import logging

log = logging.getLogger('ckanext.kata.controller')


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
