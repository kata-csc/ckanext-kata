import logging

from rdflib import URIRef, BNode, Literal
from rdflib.namespace import Namespace, RDF

from ckanext.dcat.profiles import RDFProfile

from ckanext.kata.helpers import json_to_list, convert_language_code, is_url, get_if_url, get_download_url
from ckan.lib.helpers import url_for
from ckanext.kata.utils import get_pids_by_type

log = logging.getLogger(__name__)

DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
ORG = Namespace("http://www.w3.org/ns/org#")
FRAPO = Namespace("http://purl.org/cerif/frapo/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SPDX = Namespace('http://spdx.org/rdf/terms#')

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'adms': ADMS,
    'org': ORG,
    'frapo': FRAPO,
    'rdfs': RDFS,
    'foaf': FOAF,
    'spdx': SPDX
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

        # TODO: do we need to add CatalogRecord?

        # Basic fields
        # items = [
        #     ('url', DCAT.landingPage, None, URIRef),  # disabled in old serializer
        #     ('identifier', DCT.identifier, ['guid', 'id'], Literal),  # TODO
        #     ('version', OWL.versionInfo, ['dcat_version'], Literal),
        #     ('version_notes', ADMS.versionNotes, None, Literal),
        #     ('frequency', DCT.accrualPeriodicity, None, Literal),
        #     ('access_rights', DCT.accessRights, None, Literal),  # TODO
        #     ('dcat_type', DCT.type, None, Literal),
        #     ('provenance', DCT.provenance, None, Literal),
        #     ('provenance', DCT.provenance, None, Literal),
        # ]
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

        # Etsin: Agents
        for agent in dataset_dict.get('agent', []):
            agent_role = agent.get('role')

            # Rights Holders
            if agent_role in ['owner', 'distributor']:
                name = agent.get('name', None)

                if agent_role == 'owner':
                    if not get_if_url(agent.get('name')):
                        name = agent.get('name', agent.get('organisation', ''))
                    nodetype = DCT.rightsHolder

                if agent_role == 'distributor':
                    nodetype = DCT.publisher

                agent_node_ref = BNode()
                g.add((agent_node_ref, RDF.type, FOAF.Agent))
                g.add((dataset_ref, nodetype, agent_node_ref))
                g.add((agent_node_ref, FOAF.name, Literal(name)))

            # Authors
            if agent_role in ['author', 'contributor']:
                if agent_role == 'author':
                    nodetype = DCT.creator

                if agent_role == 'contributor':
                    nodetype = DCT.contributor

                organization_ref = BNode()
                agent_ref = BNode()
                memberof_ref = BNode()
                creator_ref = BNode()

                g.add((organization_ref, FOAF.name, Literal(agent.get('organisation', None))))
                g.add((memberof_ref, FOAF.organization, organization_ref))
                g.add((agent_ref, ORG.memberOf, memberof_ref))
                g.add((agent_ref, FOAF.name, Literal(agent.get('name', None))))
                g.add((creator_ref, FOAF.Agent, agent_ref))
                g.add((dataset_ref, nodetype, creator_ref))

            # Funders
            if agent.get('role') == 'funder':
                organization_ref = BNode()
                memberof_ref = BNode()
                project_ref = BNode()
                isoutputof_ref = BNode()

                if agent.get('URL'):
                    g.add((project_ref, FOAF.homepage, Literal(agent.get('URL', None))))

                if agent.get('fundingid'):
                    g.add((project_ref, RDFS.comment, Literal(agent.get('fundingid', None))))

                g.add((organization_ref, FOAF.name, Literal(agent.get('organisation', None))))
                g.add((memberof_ref, FOAF.organization, organization_ref))
                g.add((project_ref, ORG.memberOf, memberof_ref))
                g.add((project_ref, FOAF.name, Literal(agent.get('name', None))))
                g.add((isoutputof_ref, FOAF.Project, project_ref))
                g.add((dataset_ref, FRAPO.isOutputOf, isoutputof_ref))

        # Etsin: Publishers
        for contact in dataset_dict.get('contact'):
            agent_node_ref = BNode()
            g.add((agent_node_ref, RDF.type, FOAF.Agent))
            g.add((dataset_ref, DCT.publisher, agent_node_ref))
            g.add((agent_node_ref, FOAF.name, Literal(contact.get('name', None))))

            if contact.get('email') != 'hidden':
                email = contact.get('email', None)
                g.add((agent_node_ref, FOAF.mbox, URIRef("mailto:" + email)))

            if contact.get('URL'):
                url = contact.get('URL', None)
                g.add((agent_node_ref, FOAF.homepage, URIRef(url)))

            if contact.get('phone'):
                phone = contact.get('phone', None)
                g.add((agent_node_ref, FOAF.phone, URIRef("tel:" + phone)))


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

        # Etsin: Distribution
        availability_list = ['access_application', 'access_request', 'through_provider']

        checksum_ref = BNode()
        checksum_parent_ref = BNode()
        distribution_ref = BNode()
        dist_parent_ref = BNode()

        checksum = dataset_dict.get('checksum')
        algorithm = dataset_dict.get('algorithm')
        if checksum and algorithm:
            g.add((checksum_ref, SPDX.checksumValue, Literal(checksum)))
            g.add((checksum_ref, SPDX.algorithm, Literal(algorithm)))
            g.add((checksum_parent_ref, SPDX.Checksum, checksum_ref))
            g.add((distribution_ref, SPDX.checksum, checksum_parent_ref))

        if dataset_dict.get('availability') in availability_list:
            access_url = get_download_url(dataset_dict)
            g.add((distribution_ref, DCAT.accessURL, Literal(access_url)))

        if dataset_dict.get('availability') == 'direct_download':
            access_url = get_download_url(dataset_dict)
            g.add((distribution_ref, DCAT.downloadURL, Literal(access_url)))

        mimetype = dataset_dict.get('mimetype')
        if mimetype:
            g.add((distribution_ref, DCAT.mediaType, Literal(mimetype)))

        dist_format = dataset_dict.get('format')
        if dist_format:
            g.add((distribution_ref, DCT['format'], Literal(dist_format)))

        g.add((dist_parent_ref, DCAT.Distribution, distribution_ref))
        g.add((dataset_ref, DCAT.distribution, dist_parent_ref))

        #  Lists
        # items = [
        #     ('theme', DCAT.theme, None, URIRef),
        #     ('conforms_to', DCT.conformsTo, None, Literal),
        #     ('alternate_identifier', ADMS.identifier, None, Literal),
        #     ('documentation', FOAF.page, None, Literal),
        #     ('related_resource', DCT.relation, None, Literal),  # TODO
        #     ('has_version', DCT.hasVersion, None, Literal),
        #     ('is_version_of', DCT.isVersionOf, None, Literal),
        #     ('source', DCT.source, None, Literal),
        #     ('sample', ADMS.sample, None, Literal),
        # ]
        # self._add_list_triples_from_dict(dataset_dict, dataset_ref, items)

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
