'''Settings and constants for Kata CKAN extension'''

AGENT_ROLES = {
    'author': 'Author',
    'contributor': 'Contributor',
    'distributor': 'Distributor/Publisher',
    'funder': 'Funder',
    'owner': 'Owner',
    'producer': 'Producer',
}

# Ordered list of facets used in dataset page.
FACETS = ['tags', 'extras_discipline', 'authorstring', 'organizationstring', 'license_id', 'mimetypestring', 'extras_language']

# Default sorting method. Pre-selects the corresponding option on search form.
DEFAULT_SORT_BY = u'metadata_modified desc'

# Titles for all fields used in searches, should be used through helpers.get_field_titles() for translation
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
                 'mimetypestring': 'MIME',
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
                 'ext_agent': 'Agent',
                 'extras_language': 'Language',
                 'ext_extras_language': 'Language',
                 'ext_funder': 'Funder',
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
                 'ext_agent',
                 'ext_organization',
                 #'ext_groups',
                 'ext_funder',
                 #'ext_licensetext',
                 #'ext_extras_fformat',
                 #'ext_fformatstring',
                 #'ext_extras_language',
                 ]

# File types and converters used for extracting plain text from structured documents.
# The 'args' member can be used for passing extra arguments to the program in addition
# to the input file name which is always given as the first argument.
# This can be used e.g. if the command requires a specific argument to print output
# on stdout.
TEXTOUTPUTPROGS = {
    'doc': { 'exec': '/usr/bin/catdoc' },
    'html': { 'exec': '/usr/bin/w3m' },
    'odt': { 'exec': '/usr/bin/odt2txt' },
    'xls': { 'exec': '/usr/bin/xls2csv' },
    'ods': { 'exec': '/usr/bin/ods2txt' },
    'ppt': { 'exec': '/usr/bin/catppt' },
    'odp': { 'exec': '/usr/bin/odp2txt' },
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
                        'contact',
                        # 'author',
                        'langtitle',
                        # 'contact_phone',
                        # 'contact_URL',
                        # 'organization',
                        # 'owner',
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
                           'event',
                           'geographic_coverage',
                           'langdis',
                           'language',
                           'license_URL',
                           #'mimetype',
                           # 'project_funder',
                           # 'project_funding',
                           # 'project_homepage',
                           # 'project_name',
                           'pids',
                           'temporal_coverage_begin',
                           'temporal_coverage_end']

KATA_FIELDS = KATA_FIELDS_RECOMMENDED + KATA_FIELDS_REQUIRED
