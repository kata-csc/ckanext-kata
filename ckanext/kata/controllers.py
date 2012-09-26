'''Metadata based controllers for KATA.
'''

from ckan.lib.base import BaseController, c
from ckan.model import Package

from pylons import response
from vocab import Graph, URIRef, Literal, BNode
from vocab import DC, DCAT, FOAF, OWL, RDF, RDFS, UUID, VOID, OPMV, SKOS,\
                    REV, SCOVO, XSD, LICENSES

import logging

log = logging.getLogger('ckanext.kata.controller')


class MetadataController(BaseController):

    def tordf(self, id, format):
        graph = Graph()
        pkg = Package.get(id)
        data = pkg.as_dict()
        uri = URIRef(data['ckan_url']) if 'ckan_url' in data else BNode()
        graph.add((uri, DC.identifier, Literal(data["name"])))
        response.headers['Content-type'] = 'text/xml'
        if format == 'rdf':
            format = 'pretty-xml'
        return graph.serialize(format=format)
