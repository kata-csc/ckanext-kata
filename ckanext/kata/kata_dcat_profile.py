import logging

from ckan.lib.helpers import url_for

from ckanext.dcat.profiles import RDFProfile
from ckanext.kata.helpers import convert_language_code, get_download_url, \
    get_if_url, get_rightscategory, is_url, json_to_list, split_disciplines, \
    resolve_org_name
from ckanext.kata.utils import get_primary_pid, get_pids_by_type

from rdflib import BNode, Literal, URIRef
from rdflib.namespace import Namespace, RDF

log = logging.getLogger(__name__)

DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
ADMS = Namespace("http://www.w3.org/ns/adms#")
ORG = Namespace("http://www.w3.org/ns/org#")
FRAPO = Namespace("http://purl.org/cerif/frapo/")
RDFS = Namespace("http://www.w3.org/2000/01/rdf-schema#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
SPDX = Namespace('http://spdx.org/rdf/terms#')
SCHEMA = Namespace('http://schema.org/')

namespaces = {
    'dct': DCT,
    'dcat': DCAT,
    'adms': ADMS,
    'org': ORG,
    'frapo': FRAPO,
    'rdfs': RDFS,
    'foaf': FOAF,
    'spdx': SPDX,
    'schema': SCHEMA
}


class KataDcatProfile(RDFProfile):
    '''
        A custom profile to add KATA fields to the ckanext-dcat RDF serializer.
        Modified from EuropeanDCATAPProfile
    '''

    def _add_translated_triple_from_dict(self, _dict, subject, predicate, key,
                                         fallback=None):
        """
            Creates an RDF triple from a Kata language string
            {"fin": "Otsikko", "eng": "Title"} ->
            <dct:title xml:lang="fi">Otsikko</dct:title>
            <dct:title xml:lang="en">Title</dct:title>
        """

        value = self._get_dict_value(_dict, key)
        if not value and fallback:
            value = self._get_dict_value(_dict, fallback)
        for item in json_to_list(value):
            lang = convert_language_code(
                item.get('lang'), 'alpha2', throw_exceptions=False)
            params = (subject, predicate, Literal(
                item.get('value'), lang=lang))
            self.g.add(params)

    def graph_from_dataset(self, dataset_dict, dataset_ref):

        g = self.g

        for prefix, namespace in namespaces.iteritems():
            g.bind(prefix, namespace)

        g.add((dataset_ref, RDF.type, DCAT.Dataset))

        # Etsin: homepage
        uri = url_for(controller='package', action='read',
                      id=dataset_dict.get('name'), qualified=True)
        g.add((dataset_ref, FOAF.homepage, URIRef(uri)))

        # Etsin: primary identifier
        g.add((dataset_ref, ADMS.identifier, URIRef(get_primary_pid(dataset_dict))))

        # Etsin: Relation identifiers
        relation_pids = get_pids_by_type('relation', dataset_dict)
        for rpid in relation_pids:
            if rpid.get('relation') == 'isNewVersionOf' or rpid.get('relation') == 'isPreviousVersionOf':
                g.add((dataset_ref, DCT.isVersionOf, URIRef(rpid.get('id'))))
            elif rpid.get('relation') == 'hasPart':
                g.add((dataset_ref, DCT.hasPart, URIRef(rpid.get('id'))))
            elif rpid.get('relation') == 'isPartOf':
                g.add((dataset_ref, DCT.isPartOf, URIRef(rpid.get('id'))))
            else:
                g.add((dataset_ref, DCT.identifier, URIRef(rpid.get('id'))))

        # Etsin: Title and Description, including translations
        items = [
            (DCT.title, 'langtitle', 'title'),
            (DCT.description, 'notes'),
        ]

        for item in items:
            self._add_translated_triple_from_dict(
                dataset_dict, dataset_ref, *item)

        # Etsin: Agents
        for agent in dataset_dict.get('agent', []):
            agent_role = agent.get('role')
            agent_id = agent.get('id')

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
                if agent_id:
                    g.add((agent_node_ref, DCT.identifier, Literal(agent_id)))

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

                g.add((organization_ref, FOAF.name, Literal(
                    agent.get('organisation', None))))
                g.add((memberof_ref, FOAF.organization, organization_ref))
                g.add((agent_ref, ORG.memberOf, memberof_ref))
                g.add((agent_ref, FOAF.name, Literal(agent.get('name', None))))
                g.add((creator_ref, FOAF.Agent, agent_ref))
                g.add((dataset_ref, nodetype, creator_ref))

                if agent_id:
                    g.add((agent_ref, DCT.identifier, Literal(agent_id)))


            # Funders
            if agent.get('role') == 'funder':
                organization_ref = BNode()
                memberof_ref = BNode()
                project_ref = BNode()
                isoutputof_ref = BNode()

                agent_url = agent.get('URL')
                if agent_url:
                    g.add((project_ref, FOAF.homepage, Literal(agent_url)))

                funding_id = agent.get('fundingid')
                if funding_id:
                    g.add((project_ref, RDFS.comment, Literal(funding_id)))

                g.add((organization_ref, FOAF.name, Literal(
                    agent.get('organisation', None))))
                g.add((memberof_ref, FOAF.organization, organization_ref))
                g.add((project_ref, ORG.memberOf, memberof_ref))

                agent_name = agent.get('name', None)
                g.add((project_ref, FOAF.name, Literal(agent_name)))

                if agent_id:
                    g.add((project_ref, DCT.identifier, Literal(agent_id)))

                g.add((isoutputof_ref, FOAF.Project, project_ref))
                g.add((dataset_ref, FRAPO.isOutputOf, isoutputof_ref))

        # Etsin: Publishers
        for contact in dataset_dict.get('contact'):
            agent_node_ref = BNode()
            agent_id = contact.get('id')

            g.add((agent_node_ref, RDF.type, FOAF.Agent))
            g.add((dataset_ref, DCT.publisher, agent_node_ref))

            contact_name = contact.get('name', None)
            g.add((agent_node_ref, FOAF.name, Literal(contact_name)))
            if agent_id:
                g.add((agent_node_ref, DCT.identifier, Literal(agent_id)))

            contact_email = contact.get('email')
            if contact_email and contact_email != 'hidden':
                g.add((agent_node_ref, FOAF.mbox,
                       URIRef("mailto:" + contact_email)))

            contact_url = contact.get('URL')
            if contact_url:
                g.add((agent_node_ref, FOAF.homepage, URIRef(contact_url)))

            contact_phone = contact.get('phone')
            if contact_phone:
                g.add((agent_node_ref, FOAF.phone,
                       URIRef("tel:" + contact_phone)))

        # Etsin: Organization
        organization_name = resolve_org_name(dataset_dict.get('owner_org'))
        publisher_ref = BNode()
        g.add((dataset_ref, DCT.publisher, publisher_ref))
        g.add((publisher_ref, FOAF.organization, Literal(organization_name)))

        # Etsin: Tags - can be URLs or user inputted keywords
        # TODO: resolve URLs from Finto. Currently get_label_for_uri() breaks
        # RDFlib.
        for tag in dataset_dict.get('tags', []):
            display_name = tag.get('display_name')
            g.add((dataset_ref, DCAT.keyword, Literal(display_name)))
            tag_name = tag.get('name')
            if is_url(tag_name):
                g.add((dataset_ref, DCAT.theme, URIRef(tag_name)))

        # Etsin: Dates
        # Peter: Issued-field is new. This used to be inside CatalogRecord.
        items = [
            ('issued', DCT.issued, ['metadata_created'], Literal),
            ('modified', DCT.modified, ['metadata_modified'], Literal),
        ]
        self._add_date_triples_from_dict(dataset_dict, dataset_ref, items)

        # Etsin: Events
        for event in dataset_dict.get('event', []):
            event_ref = BNode()
            g.add((dataset_ref, DCT.event, event_ref))
            g.add((event_ref, DCT.type, Literal(event.get('type'))))
            g.add((event_ref, DCT.creator, Literal(event.get('who'))))
            g.add((event_ref, DCT.date, Literal(str(event.get('when')))))
            g.add((event_ref, DCT.description, Literal(event.get('descr'))))

        # Etsin: Citation
        citation = dataset_dict.get('citation')
        if citation:
            g.add((dataset_ref, DCT.bibliographicCitation, Literal(citation)))      


        # Etsin: Distribution
        availability_list = ['access_application',
                             'access_request', 'through_provider']

        checksum_ref = BNode()
        checksum_parent_ref = BNode()
        distribution_ref = BNode()
        dist_parent_ref = BNode()

        if dataset_dict.get('availability') == 'direct_download':
            access_url = get_download_url(dataset_dict)
            g.add((distribution_ref, DCAT.downloadURL, Literal(access_url)))

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

        mimetype = dataset_dict.get('mimetype')
        if mimetype:
            g.add((distribution_ref, DCAT.mediaType, Literal(mimetype)))

        dist_format = dataset_dict.get('format')
        if dist_format:
            g.add((distribution_ref, DCT['format'], Literal(dist_format)))

        g.add((dist_parent_ref, DCAT.Distribution, distribution_ref))
        g.add((dataset_ref, DCAT.distribution, dist_parent_ref))

        # Etsin: Disciplines
        disciplines = dataset_dict.get('discipline', '')
        for discipline in split_disciplines(disciplines):
            if is_url(discipline):
                disc = URIRef(discipline)

            else:
                disc = Literal(discipline)
            g.add((dataset_ref, DCT.subject, disc))

        # Etsin: Rights Declaration
        # Peter: There's no way to add an xmlns attribute under
        # the parent <DCT:rights> in rdflib
        category, declarations = get_rightscategory(dataset_dict)
        declaration_strings = ''
        for declaration in declarations:
            declaration_strings += u'<RightsDeclaration>{}</RightsDeclaration>\n'\
                .format(declaration)
        xml_string = u'<RightsDeclarationMD RIGHTSCATEGORY="{}" \
            xmlns="http://www.loc.gov/METS/" >\n{}</RightsDeclarationMD>'\
            .format(category, declaration_strings)

        license_url = dataset_dict.get('license_URL')

        rights_ref = BNode()
        g.add((dataset_ref, DCT.rights, rights_ref))
        g.add((rights_ref, DCT.RightsStatement, Literal(
            xml_string, datatype=RDF.XMLLiteral)))
        g.add((rights_ref, DCT.RightsStatement, Literal(license_url)))


        # Etsin: Spatial
        coverage = dataset_dict.get('geographic_coverage')
        if coverage:
            spatial_ref = BNode()
            location_ref = BNode()
            g.add((location_ref, RDFS.label, Literal(coverage)))
            g.add((spatial_ref, DCT.Location, location_ref))
            g.add((dataset_ref, DCT.spatial_ref, spatial_ref))

        # Etsin: Temporal
        # Peter: hasBeginning and hasEnd left out
        temporal_coverage_begin = dataset_dict.get('temporal_coverage_begin')
        temporal_coverage_end = dataset_dict.get('temporal_coverage_end')
        if temporal_coverage_begin or temporal_coverage_end:
            temporal_extent = BNode()

            g.add((temporal_extent, RDF.type, DCT.PeriodOfTime))
            if temporal_coverage_begin:
                self._add_date_triple(
                    temporal_extent, SCHEMA.startDate, temporal_coverage_begin)

            if temporal_coverage_end:
                self._add_date_triple(
                    temporal_extent, SCHEMA.endDate, temporal_coverage_end)

            g.add((dataset_ref, DCT.temporal, temporal_extent))

        # Etsin: language field needs to be stripped from spaces
        langs = self._get_dict_value(dataset_dict, 'language', '').split(', ')
        for lang in langs:
            params = (dataset_ref, DCAT.language, Literal(lang))
            self.g.add(params)
