'''Metadata based controllers for KATA.
'''

from ckan.lib.base import BaseController, c, h
from ckan.model import Package

from pylons import response, config

from rdflib.term import Identifier, Statement, Node, Variable

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
        uri = BNode()
        graph.add((uri, DC.identifier, Literal(data["name"])\
                            if 'identifier' not in data["extras"]\
                            else URIRef(data["extras"]["identifier"])))
        graph.add((uri, DC.modified, Literal(data["metadata_modified"],
                                             datatype=XSD.date)))
        graph.add((uri, DC.title, Literal(data["title"])))
        if data["license"]:
            graph.add((uri, DC.rights, Literal(data["license"])))
        self.roles = {}
        for extra in data["extras"]:
            self._check_and_gather_role(extra)
        for key, value in self.roles.iteritems():
            if key in ('Author', 'Producer', 'Publisher'):
                if key == 'Author':
                    for val in value:
                        id = Identifier(FOAF.Person)
                        graph.add((uri, DC.creator, id))
                        graph.add((id, FOAF.name, Literal(data["extras"][val])))
                if key == 'Producer':
                    for val in value:
                        id = Identifier(FOAF.Person)
                        graph.add((uri, DC.contributor, id))
                        graph.add((id, FOAF.name, Literal(data["extras"][val])))
                if key == 'Publisher':
                    for val in value:
                        id = Identifier(FOAF.Person)
                        graph.add((uri, DC.publisher, id))
                        graph.add((id, FOAF.name, Literal(data["extras"][val])))
        for tag in data["tags"]:
            graph.add((uri, DC.subject, Literal(tag)))
        graph.add((uri, DC.description, Literal(data["notes"])))
        if data["url"]:
            graph.add((uri, DC.source, URIRef(data["url"])))
        for res in data["resources"]:
            extra = Identifier(h.url_for(controller='package',
                                         action='resource_read',
                                         id=data['id'],
                                         resource_id=res['id']))
            graph.add((uri, DC.relation, extra))
            if res["url"]:
                graph.add((extra, DC.isReferencedBy, URIRef(res["url"])))
            if res["size"]:
                graph.add((extra, DC.extent, Literal(res['size'])))
            if res["format"]:
                graph.add((extra, DC.hasFormat, Literal(res['format'])))
        response.headers['Content-type'] = 'text/xml'
        if format == 'rdf':
            format = 'pretty-xml'
        return graph.serialize(format=format)
