'''Settings and constants for Kata CKAN extension'''

# Facets used in Solr queries
# Facets need also to be changed to search.html. This all should be fixed in newer CKAN versions with IFacets interface.
FACETS = ['groups','tags','extras_fformat','license','authorstring','organizationstring','extras_language']

# Default sorting method. Pre-selects the corresponding option on search form.
DEFAULT_SORT_BY = u'metadata_modified desc'

FIELD_TITLES = {'organizationstring': _('Organization'),
                'tags': _('Keywords'),
                'extras_fformat': _('File formats'),
                'groups': _('Discipline'),
                'license': _('Licence'),
                'authorstring': _('Author'),
                'extras_language': _('Language'),
                'title': _('Title'),
                }
