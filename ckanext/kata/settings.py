'''Settings and constants for Kata CKAN extension'''


# Facets used in Solr queries
# Facets need also to be changed to search.html. This all should be fixed in newer CKAN versions with IFacets interface.
FACETS = ['extras_discipline', 'tags', 'mimetypestring', 'license_id', 'authorstring', 'organizationstring', 'extras_language']

# Default sorting method. Pre-selects the corresponding option on search form.
DEFAULT_SORT_BY = u'metadata_modified desc'

# Titles for all fields used in searches, should be used through get_field_titles() for translation
_FIELD_TITLES = {'organizationstring': 'Organization',
                 'ext_organizationstring': 'Organization',
                 'ext_organization': 'Organization',
                 'tags': 'Keywords',
                 'ext_tags': 'Keywords',
                 'ext_pids': 'Permanent identifiers',
                 'extras_fformat': 'File formats',
                 'ext_extras_fformat': 'File formats',
                 'fformatstring': 'File formats',
                 'ext_fformatstring': 'File formats',
                 'mimetypestring': 'MIME type',
                 #'groups': 'Discipline',
                 #'ext_groups': 'Discipline',
                 'ext_discipline': 'Discipline',
                 'extras_discipline': 'Discipline',
                 'license': 'License',
                 'license_id': 'License',
                 'ext_license': 'License',
                 'ext_licensetext': 'License',
                 'authorstring': 'Author',
                 'ext_authorstring': 'Author',
                 'ext_author': 'Author',
                 'ext_actor': 'Actor',
                 'extras_language': 'Language',
                 'ext_extras_language': 'Language',
                 'ext_extras_funder': 'Funder',
                 'title': 'Title',
                 'ext_title': 'Title',
                 'ext_text': 'All fields',
                 }

# Ordered list of fields for advanced search. First one will be used as the default search field.
SEARCH_FIELDS = ['ext_text',
                 'ext_author',
                 'ext_title',
                 'ext_tags',
                 'ext_pids',
                 'ext_actor',
                 'ext_organization',
                 #'ext_groups',
                 'ext_extras_funder',
                 'ext_licensetext',
                 #'ext_extras_fformat',
                 'ext_fformatstring',
                 'ext_extras_language',
                 ]

# File types and converters used by DataMiningController.
TEXTOUTPUTPROGS = {
    'doc': '/usr/bin/catdoc',
    'html': '/usr/bin/w3m',
    'odt': '/usr/bin/odt2txt',
    'xls': '/usr/bin/xls2csv',
    'ods': '/usr/bin/ods2txt',
    'ppt': '/usr/bin/catppt',
    'odp': '/usr/bin/odp2txt',
    }

# Text string to use for when dataset's URL is not known. Changing might cause issues as this is also CKAN default.
DATASET_URL_UNKNOWN = 'http://'

# Text string for dataset's resource.resource_type
RESOURCE_TYPE_DATASET = 'dataset'

# All availability URL fields used with different availability options
AVAILABILITY_OPTIONS = {'access_application': 'access_application_URL',
                        'access_request': 'access_request_URL',
                        'contact_owner': None,
                        'direct_download': None,
                        'through_provider': 'through_provider_URL',
                        }

# Required extras fields
KATA_FIELDS_REQUIRED = ['agent',
                        'availability',
                        # 'author',
                        'contact_URL',
                        'langdis',
                        'language',
                        # 'organization',
                        # 'owner',
                        'contact_phone',
                        'pids',
                        # 'projdis',
                        #'maintainer_email',
                        #'version_PID'
                        ]

# Recommended extras fields
KATA_FIELDS_RECOMMENDED = ['access_application_new_form',
                           'access_application_URL',
                           'access_request_URL',
                           'through_provider_URL',
                           #'algorithm',
                           #'direct_download_URL',
                           'discipline',
                           'evdescr',
                           'evtype',
                           'evwhen',
                           'evwho',
                           'geographic_coverage',
                           'license_URL',
                           #'mimetype',
                           # 'project_funder',
                           # 'project_funding',
                           # 'project_homepage',
                           # 'project_name',
                           'temporal_coverage_begin',
                           'temporal_coverage_end']

KATA_FIELDS = KATA_FIELDS_RECOMMENDED + KATA_FIELDS_REQUIRED


def get_field_titles(_):
    '''
    Get correctly translated titles for search fields

    :param _: gettext translator
    :return: dict of titles for fields
    '''

    translated_field_titles = {}

    for k, v in _FIELD_TITLES.iteritems():
        translated_field_titles[k] = _(v)

    return translated_field_titles


def get_field_title(key, _):
    '''
    Get correctly translated title for one search field

    :param _: gettext translator
    :return: dict of titles for fields
    '''

    return _(_FIELD_TITLES[key])
