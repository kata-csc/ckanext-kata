import datetime
import json
import logging

from dateutil.parser import parse as parse_date

from pylons import config

import rdflib
from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF, XSD, SKOS, RDFS

from geomet import wkt, InvalidGeoJSONException

from ckan.plugins import toolkit

from ckanext.dcat.utils import resource_uri, publisher_uri_from_dataset_dict
from ckanext.dcat.profiles import RDFProfile

from ckanext.kata.helpers import json_to_list, convert_language_code, is_url, get_label_for_uri
from ckan.lib.helpers import url_for
from ckanext.kata.utils import get_pids_by_type

log = logging.getLogger(__name__)

DC = Namespace("http://purl.org/dc/terms/")
DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SCHEMA = Namespace('http://schema.org/')
TIME = Namespace('http://www.w3.org/2006/time')
LOCN = Namespace('http://www.w3.org/ns/locn#')
GSP = Namespace('http://www.opengis.net/ont/geosparql#')
OWL = Namespace('http://www.w3.org/2002/07/owl#')
SPDX = Namespace('http://spdx.org/rdf/terms#')
DCES = Namespace("http://purl.org/dc/elements/1.1/")
LICENSES = Namespace("http://purl.org/okfn/licenses/")
LOCAL = Namespace("http://opendatasearch.org/schema#")
OPMV = Namespace("http://purl.org/net/opmv/ns#")
REV = Namespace("http://purl.org/stuff/rev#")
SCOVO = Namespace("http://purl.org/NET/scovo#")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")
VOID = Namespace("http://rdfs.org/ns/void#")
UUID = Namespace("urn:uuid:")
GEOJSON_IMT = 'https://www.iana.org/assignments/media-types/application/vnd.geo+json'

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'adms': ADMS,
    #'schema': SCHEMA,
    #'locn': LOCN,
    #'gsp': GSP,
    #"rdf": RDF,
    #"rdfs": RDFS,
    #"owl": OWL,
    #"dc": DC,
    "foaf": FOAF,
    #"opmv": OPMV,
    #"skos": SKOS,
    #"time": TIME,
    #"void": VOID,
    #"vcard": VCARD,
    #"local": LOCAL,
    #"rev": REV,
    #"scovo": SCOVO,
    #"licenses": LICENSES
}


class KataDcatProfile(RDFProfile):
    '''
        A custom profile to add KATA fields to the ckanext-dcat RDF serializer.
        Modified from EuropeanDCATAPProfile
    '''

    def _add_translated_triple_from_dict(self, _dict, subject, predicate, key, fallback=None):
        """
            Creates an RDF triple from a Kata language string
            self._add_translated_triple_from_dict(dataset_dict, dataset_ref, DCT.title, 'langtitle', 'title')
            {"fin": "Otsikko", "eng": "Title"} ->
            <dct:title xml:lang="fi">Otsikko</dct:title>
            <dct:title xml:lang="en">Title</dct:title>
        """

        value = self._get_dict_value(_dict, key)
        if not value and fallback:
            value = self._get_dict_value(_dict, fallback)
        for item in json_to_list(value):
            lang = convert_language_code(item.get('lang'), 'alpha2', throw_exceptions=False)
            params = (subject, predicate, Literal(item.get('value'), lang=lang))
            self.g.add(params)

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        g = self.g

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        g.add((dataset_ref, RDF.type, DCAT.Dataset))

        # TODO:
        # How to add CatalogRecord?

        # Basic fields
        # TODO: check each field name
        items = [
            #('url', DCAT.landingPage, None, URIRef),  # disabled in old serializer
            #('identifier', DCT.identifier, ['guid', 'id'], Literal),  # TODO
            #('version', OWL.versionInfo, ['dcat_version'], Literal),
            #('version_notes', ADMS.versionNotes, None, Literal),
            #('frequency', DCT.accrualPeriodicity, None, Literal),
            #('access_rights', DCT.accessRights, None, Literal),  # TODO
            #('dcat_type', DCT.type, None, Literal),
            #('provenance', DCT.provenance, None, Literal),
            #('provenance', DCT.provenance, None, Literal),
        ]
        #self._add_triples_from_dict(dataset_dict, dataset_ref, items)

        # Etsin: homepage
        uri = url_for(controller='package', action='read', id=dataset_dict.get('name'), qualified=True)
        g.add((dataset_ref, FOAF.homepage, URIRef(uri)))

        # Etsin: primary identifiers
        data_pids = get_pids_by_type('data', dataset_dict)
        for pid in data_pids:
            g.add((dataset_ref, ADMS.identifier, URIRef(pid.get('id'))))

        version_pids = get_pids_by_type('version', dataset_dict)
        for pid in version_pids:
            g.add((dataset_ref, DCT.identifier, URIRef(pid.get('id'))))
            g.add((dataset_ref, DCT.isVersionOf, URIRef(pid.get('id'))))

        # Etsin: Title and Description, including translations
        items = [
            (DCT.title, 'langtitle', 'title'),
            (DCT.description, 'notes'),
        ]

        for item in items:
            self._add_translated_triple_from_dict(dataset_dict, dataset_ref, *item)

        # Tags
        # Etsin: tags can be URLs or user inputted keywords
        # TODO: resolve URLs from Finto. Currently get_label_for_uri() breaks RDFlib.
        for tag in dataset_dict.get('tags', []):
            g.add((dataset_ref, DCAT.keyword, Literal(tag.get('display_name'))))
            if is_url(tag.get('name')):
                g.add((dataset_ref, DCAT.theme, URIRef(tag.get('name'))))

        # Dates
        # Etsin: issued-field is new. This used to be inside CatalogRecord.
        items = [
            ('issued', DCT.issued, ['metadata_created'], Literal),
            ('modified', DCT.modified, ['metadata_modified'], Literal),
        ]
        self._add_date_triples_from_dict(dataset_dict, dataset_ref, items)

        #  Lists
        items = [
            #('theme', DCAT.theme, None, URIRef),
            #('conforms_to', DCT.conformsTo, None, Literal),
            #('alternate_identifier', ADMS.identifier, None, Literal),
            #('documentation', FOAF.page, None, Literal),
            #('related_resource', DCT.relation, None, Literal),  # TODO
            #('has_version', DCT.hasVersion, None, Literal),
            #('is_version_of', DCT.isVersionOf, None, Literal),
            #('source', DCT.source, None, Literal),
            #('sample', ADMS.sample, None, Literal),
        ]
        self._add_list_triples_from_dict(dataset_dict, dataset_ref, items)

        # Etsin: language field need to be stripped from spaces
        langs = self._get_dict_value(dataset_dict, 'language').split(', ')
        for lang in langs:
            params = (dataset_ref, DCAT.language, Literal(lang))
            self.g.add(params)

        # # Contact details
        # if any([
        #     self._get_dataset_value(dataset_dict, 'contact_uri'),
        #     self._get_dataset_value(dataset_dict, 'contact_name'),
        #     self._get_dataset_value(dataset_dict, 'contact_email'),
        #     self._get_dataset_value(dataset_dict, 'maintainer'),
        #     self._get_dataset_value(dataset_dict, 'maintainer_email'),
        #     self._get_dataset_value(dataset_dict, 'author'),
        #     self._get_dataset_value(dataset_dict, 'author_email'),
        # ]):

        #     contact_uri = self._get_dataset_value(dataset_dict, 'contact_uri')
        #     if contact_uri:
        #         contact_details = URIRef(contact_uri)
        #     else:
        #         contact_details = BNode()

        #     g.add((contact_details, RDF.type, VCARD.Organization))
        #     g.add((dataset_ref, DCAT.contactPoint, contact_details))

        #     items = [
        #         ('contact_name', VCARD.fn, ['maintainer', 'author'], Literal),
        #         ('contact_email', VCARD.hasEmail, ['maintainer_email',
        #                                            'author_email'], Literal),
        #     ]

        #     self._add_triples_from_dict(dataset_dict, contact_details, items)

        # # Publisher
        # if any([
        #     self._get_dataset_value(dataset_dict, 'publisher_uri'),
        #     self._get_dataset_value(dataset_dict, 'publisher_name'),
        #     dataset_dict.get('organization'),
        # ]):

        #     publisher_uri = publisher_uri_from_dataset_dict(dataset_dict)
        #     if publisher_uri:
        #         publisher_details = URIRef(publisher_uri)
        #     else:
        #         # No organization nor publisher_uri
        #         publisher_details = BNode()

        #     g.add((publisher_details, RDF.type, FOAF.Organization))
        #     g.add((dataset_ref, DCT.publisher, publisher_details))

        #     publisher_name = self._get_dataset_value(dataset_dict, 'publisher_name')
        #     if not publisher_name and dataset_dict.get('organization'):
        #         publisher_name = dataset_dict['organization']['title']

        #     g.add((publisher_details, FOAF.name, Literal(publisher_name)))
        #     # TODO: It would make sense to fallback these to organization
        #     # fields but they are not in the default schema and the
        #     # `organization` object in the dataset_dict does not include
        #     # custom fields
        #     items = [
        #         ('publisher_email', FOAF.mbox, None, Literal),
        #         ('publisher_url', FOAF.homepage, None, URIRef),
        #         ('publisher_type', DCT.type, None, Literal),
        #     ]

        #     self._add_triples_from_dict(dataset_dict, publisher_details, items)

        # # Temporal
        # start = self._get_dataset_value(dataset_dict, 'temporal_start')
        # end = self._get_dataset_value(dataset_dict, 'temporal_end')
        # if start or end:
        #     temporal_extent = BNode()

        #     g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
        #     if start:
        #         self._add_date_triple(temporal_extent, SCHEMA.startDate, start)
        #     if end:
        #         self._add_date_triple(temporal_extent, SCHEMA.endDate, end)
        #     g.add((dataset_ref, DCT.temporal, temporal_extent))

        # # Spatial
        # spatial_uri = self._get_dataset_value(dataset_dict, 'spatial_uri')
        # spatial_text = self._get_dataset_value(dataset_dict, 'spatial_text')
        # spatial_geom = self._get_dataset_value(dataset_dict, 'spatial')

        # if spatial_uri or spatial_text or spatial_geom:
        #     if spatial_uri:
        #         spatial_ref = URIRef(spatial_uri)
        #     else:
        #         spatial_ref = BNode()

        #     g.add((spatial_ref, RDF.type, DCT.Location))
        #     g.add((dataset_ref, DCT.spatial, spatial_ref))

        #     if spatial_text:
        #         g.add((spatial_ref, SKOS.prefLabel, Literal(spatial_text)))

        #     if spatial_geom:
        #         # GeoJSON
        #         g.add((spatial_ref,
        #                LOCN.geometry,
        #                Literal(spatial_geom, datatype=GEOJSON_IMT)))
        #         # WKT, because GeoDCAT-AP says so
        #         try:
        #             g.add((spatial_ref,
        #                    LOCN.geometry,
        #                    Literal(wkt.dumps(json.loads(spatial_geom),
        #                                      decimals=4),
        #                            datatype=GSP.wktLiteral)))
        #         except (TypeError, ValueError, InvalidGeoJSONException):
        #             pass

        # # Resources
        # for resource_dict in dataset_dict.get('resources', []):

        #     distribution = URIRef(resource_uri(resource_dict))

        #     g.add((dataset_ref, DCAT.distribution, distribution))

        #     g.add((distribution, RDF.type, DCAT.Distribution))

        #     #  Simple values
        #     items = [
        #         ('name', DCT.title, None, Literal),
        #         ('description', DCT.description, None, Literal),
        #         ('status', ADMS.status, None, Literal),
        #         ('rights', DCT.rights, None, Literal),
        #         ('license', DCT.license, None, Literal),
        #     ]

        #     self._add_triples_from_dict(resource_dict, distribution, items)

        #     #  Lists
        #     items = [
        #         ('documentation', FOAF.page, None, Literal),
        #         ('language', DCT.language, None, Literal),
        #         ('conforms_to', DCT.conformsTo, None, Literal),
        #     ]
        #     self._add_list_triples_from_dict(resource_dict, distribution, items)

        #     # Format
        #     if '/' in resource_dict.get('format', ''):
        #         g.add((distribution, DCAT.mediaType,
        #                Literal(resource_dict['format'])))
        #     else:
        #         if resource_dict.get('format'):
        #             g.add((distribution, DCT['format'],
        #                    Literal(resource_dict['format'])))

        #         if resource_dict.get('mimetype'):
        #             g.add((distribution, DCAT.mediaType,
        #                    Literal(resource_dict['mimetype'])))

        #     # URL
        #     url = resource_dict.get('url')
        #     download_url = resource_dict.get('download_url')
        #     if download_url:
        #         g.add((distribution, DCAT.downloadURL, URIRef(download_url)))
        #     if (url and not download_url) or (url and url != download_url):
        #         g.add((distribution, DCAT.accessURL, URIRef(url)))

        #     # Dates
        #     items = [
        #         ('issued', DCT.issued, None, Literal),
        #         ('modified', DCT.modified, None, Literal),
        #     ]

        #     self._add_date_triples_from_dict(resource_dict, distribution, items)

        #     # Numbers
        #     if resource_dict.get('size'):
        #         try:
        #             g.add((distribution, DCAT.byteSize,
        #                    Literal(float(resource_dict['size']),
        #                            datatype=XSD.decimal)))
        #         except (ValueError, TypeError):
        #             g.add((distribution, DCAT.byteSize,
        #                    Literal(resource_dict['size'])))
        #     # Checksum
        #     if resource_dict.get('hash'):
        #         checksum = BNode()
        #         g.add((checksum, SPDX.checksumValue,
        #                Literal(resource_dict['hash'],
        #                        datatype=XSD.hexBinary)))

        #         if resource_dict.get('hash_algorithm'):
        #             if resource_dict['hash_algorithm'].startswith('http'):
        #                 g.add((checksum, SPDX.algorithm,
        #                        URIRef(resource_dict['hash_algorithm'])))
        #             else:
        #                 g.add((checksum, SPDX.algorithm,
        #                        Literal(resource_dict['hash_algorithm'])))
        #         g.add((distribution, SPDX.checksum, checksum))
