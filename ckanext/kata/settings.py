# coding=utf8
# '''Settings and constants for Kata CKAN extension'''

from ckan.common import OrderedDict
from pylons.i18n.translation import gettext_noop as N_

PID_TYPES = ['data', 'metadata', 'version']

# Overridden CKAN role permissions
ROLE_PERMISSIONS = OrderedDict([
    ('admin', ['admin']),
    ('editor', ['admin']),
    ('member', ['read', 'create_dataset']),
])

ORGANIZATION_MEMBER_PERMISSIONS = {
    # ORGANIZATION_MEMBER_PERMISSIONS format:
    # (user role, target original role, target final role, user == target): has permission to modify role

    # Permission to delete a role is given if one has permission to change role to 'member'.

    ('admin', 'admin', 'admin', True):      False,
    ('admin', 'admin', 'admin', False):     False,
    ('admin', 'admin', 'editor', True):     False,
    ('admin', 'admin', 'editor', False):    False,
    ('admin', 'admin', 'member', True):     False,  # Admin should not be able to delete oneself
    ('admin', 'admin', 'member', False):    False,

    ('admin', 'editor', 'admin', False):    False,
    ('admin', 'editor', 'editor', False):   True,
    ('admin', 'editor', 'member', False):   True,

    ('admin', 'member', 'admin', False):    False,
    ('admin', 'member', 'editor', False):   True,
    ('admin', 'member', 'member', False):   True,

    ('editor', 'admin', 'admin', False):    False,
    ('editor', 'admin', 'editor', False):   False,
    ('editor', 'admin', 'member', False):   False,

    ('editor', 'editor', 'admin', True):    False,
    ('editor', 'editor', 'admin', False):    False,
    ('editor', 'editor', 'editor', True):    True,
    ('editor', 'editor', 'editor', False):    False,
    ('editor', 'editor', 'member', True):    True,
    ('editor', 'editor', 'member', False):    False,

    ('editor', 'member', 'admin', False):    False,
    ('editor', 'member', 'editor', False):   False,
    ('editor', 'member', 'member', False):   True,
}

AGENT_ROLES = {
    'author': N_('Author'),
    'contributor': N_('Contributor'),
    'distributor': N_('Distributor'),
    'funder': N_('Funder'),
    'owner': N_('Owner'),
    'producer': N_('Producer'),
}

# Ordered list of facets used in dataset page.
FACETS = ['tags', 'extras_discipline', 'organizationstring', 'authorstring', 'license_id', 'mimetypestring', 'extras_language']

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


# File types and converters used for extracting plain text from structured documents.
# The 'args' member can be used for passing extra arguments to the program in addition
# to the input file name which is always given as the first argument.
# The 'output' member can be used if the command requires a specific argument to
# print output on stdout.
TEXTOUTPUTPROGS = {
    'doc': { 'exec': '/usr/bin/catdoc', 'args': '', 'output': '' },
    'html': { 'exec': '/usr/bin/w3m', 'args': '', 'output': '' },
    'odt': { 'exec': '/usr/bin/odt2txt', 'args': '', 'output': '' },
    'xls': { 'exec': '/usr/bin/xls2csv', 'args': '', 'output': '' },
    'ods': { 'exec': '/usr/bin/ods2txt', 'args': '', 'output': '' },
    'ppt': { 'exec': '/usr/bin/catppt', 'args': '', 'output': '' },
    'odp': { 'exec': '/usr/bin/odp2txt', 'args': '', 'output': ''},
    'pdf': { 'exec': '/usr/bin/pdftotext', 'args': '-enc ASCII7 -nopgbrk', 'output': '-' },
    }

# Text string to use for when dataset's URL is not known. Changing might cause issues as this is also CKAN default.
DATASET_URL_UNKNOWN = 'http://'

# Text string for dataset's resource.resource_type
RESOURCE_TYPE_DATASET = 'dataset'

# All availability URL fields used with different availability options
AVAILABILITY_OPTIONS = {'access_application': 'access_application_URL',
                        'access_request': 'access_request_URL',
                        'contact_owner': None,
                        'direct_download': 'direct_download_URL',
                        'through_provider': 'through_provider_URL',
                        }

# Required extras fields
KATA_FIELDS_REQUIRED = ['agent',
                        'availability',
                        'contact',
                        ]

# Recommended extras fields
KATA_FIELDS_RECOMMENDED = ['access_application_new_form',
                           'access_application_URL',
                           'access_request_URL',
                           'discipline',
                           'event',
                           'geographic_coverage',
                           'langdis',
                           'langnotes',
                           'language',
                           'license_URL',
                           'pids',
                           'temporal_coverage_begin',
                           'temporal_coverage_end',
                           'through_provider_URL'
                           ]

KATA_FIELDS = KATA_FIELDS_RECOMMENDED + KATA_FIELDS_REQUIRED

DATAPID_TO_NAME_REGEXES = [r'[^A-Za-z0-9]', r'-']     # [pattern, replace]

# Change misleading or bad error summary names to more sane ones
ERRORS = {
    u'Pids': u'PID',
    u'Langtitle': u'Title + language',
    u'Tag string': u'Keywords',
    u'Tags': u'Keywords',
    u'Owner org': u'Owner organization',
    u'Contact': u'Distributor',
    u'Yhteydenotto': N_(u'Distributor'),
    u'Organisaatio': N_(u'Owner organization'),
    u'Accept-terms': N_(u'Terms of use'),
    u'Langnotes': u'Description + language',
    u'License URL': u'Copyright notice',
}

TRANSLATION_DUMMIES = [  # Dynamically created strings that should be translated
    N_('Go to API'),
    N_('Go to Application'),
    N_('Go to Idea'),
    N_('Go to News Article'),
    N_('Go to Paper'),
    N_('Go to Post'),
    N_('Go to Visualization'),
]


# Message strings to be automatically included in emails sent by users

# Template for the message included at the beginning of emails sent through the contact form
USER_MESSAGE_PREFIX_TEMPLATE = u"\n{sender_name} ({sender_email}) has sent you a message regarding the following dataset:\
\n\n{package_title} (Identifier: {data_pid})\n\nThe message is below.\n\n\n{sender_name} ({sender_email}) on lähettänyt sinulle viestin koskien tietoaineistoa:\
\n\n{package_title} (Tunniste: {data_pid})\n\nViesti:\n\n\n    ---\n"

# Template for the message included at the beginning of emails sent through the data access request form
DATA_REQUEST_PREFIX_TEMPLATE = u"\n{sender_name} ({sender_email}) is requesting access to data in dataset\n\n{package_title} (Identifier: {data_pid})\n\n\
for which you are currently marked as distributor.\n\nThe message is below.\n\n\n\
{sender_name} ({sender_email}) pyytää dataa, joka liittyy tietoaineistoon\n\n{package_title} (Tunniste: {data_pid})\n\nja johon sinut on merkitty jakelijaksi. \
Mukaan liitetty viesti on alla.\n\n\n    ---\n"

REPLY_TO_SENDER_NOTE = u"\n    ---\n\nPlease do not reply directly to this e-mail.\n\
If you need to reply to the sender, use the direct e-mail address above.\n\n\
Älä vastaa suoraan tähän viestiin. Jos haluat vastata lähettäjälle, \
käytä yllä olevaa sähköpostiosoitetta."
