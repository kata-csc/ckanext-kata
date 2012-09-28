'''Metadata based controllers for KATA.
'''

from ckan.lib.base import BaseController, c, h
from ckan.model import Package

from pylons import response

from rdflib.term import Identifier

from vocab import Graph, URIRef, Literal, BNode
from vocab import DC, DCES, DCAT, FOAF, OWL, RDF, RDFS, UUID, VOID, OPMV, SKOS,\
                    REV, SCOVO, XSD, LICENSES

import logging

log = logging.getLogger('ckanext.kata.controller')


class MetadataController(BaseController):

    def tordf(self, id, format):
        graph = Graph()
        pkg = Package.get(id)
        data = pkg.as_dict()
        uri = URIRef(data['ckan_url']) if 'ckan_url' in data else BNode()
        log.debug(dir(uri))
        selfref = URIRef(uri)
        graph.add((selfref, RDF.ID, Literal(pkg.id)))
        graph.add((uri, DC.identifier, Literal(data["name"])))
        log.debug(data)
        graph.add((uri, DC.modified, Literal(data["metadata_modified"],
                                             datatype=XSD.date)))
        graph.add((uri, DC.contributor, Literal(data["author_email"])))
        graph.add((uri, DC.title, Literal(data["title"])))
        graph.add((uri, DC.rights, Literal(data["license"])))
        for tag in data["tags"]:
            graph.add((uri, DC.subject, Literal(tag)))
        graph.add((uri, DC.contributor, Literal(data["author_email"])))
        if 'language' in data["extras"]:
            graph.add((uri, DC.language, Literal(data["extras"]["language"])))
        graph.add((uri, DC.description, Literal(data["notes"])))
        if data["url"]:
            graph.add((uri, DC.source, Literal(data["url"])))
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
            if res["mimetype"]:
                graph.add((extra, DC.hasFormat, Literal(res['mimetype'] + res['mimetype_inner'])))
        response.headers['Content-type'] = 'text/xml'
        if format == 'rdf':
            format = 'pretty-xml'
        return graph.serialize(format=format)
