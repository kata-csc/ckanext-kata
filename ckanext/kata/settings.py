'''Settings and constants for Kata CKAN extension'''


# Facets used in Solr queries
# Facets need also to be changed to search.html. This all should be fixed in newer CKAN versions with IFacets interface.
FACETS = ['groups','tags','extras_fformat','license','authorstring','organizationstring','extras_language']
# Facets need also to be changed to search.html. This all should be fixed in newer CKAN versions with IFacets interface.

# Default sorting method. Pre-selects the corresponding option on search form.
DEFAULT_SORT_BY = u'metadata_modified desc'

FIELD_TITLES = {'organizationstring': 'Organization',
                'tags': 'Keywords',
                'extras_fformat': 'File formats',
                'groups': 'Discipline',
                'license': 'Licence',
                'authorstring': 'Author',
                'ext_author': 'Author',
                'extras_language': 'Language',
                'title': 'Title',
                }

SEARCH_FIELDS = ['organizationstring',
                'tags',
                'extras_fformat',
                'groups',
                'license',
                'ext_author',
                'extras_language',
                'title',
                ]


def get_field_titles(_):
    '''
    Get correctly translated titles for search fields

    :param _: gettext translator
    :return: dict of titles for fields
    '''

    translated_field_titles = {}

    for k, v in FIELD_TITLES.iteritems():
        translated_field_titles[k] = _(v)

    return translated_field_titles

def get_field_title(key, _):
    '''
    Get correctly translated title for one search field

    :param _: gettext translator
    :return: dict of titles for fields
    '''

    return _(FIELD_TITLES[key])
