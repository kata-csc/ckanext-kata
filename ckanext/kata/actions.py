import re
import json
import datetime
import ckan.logic.action.get
from ckan.logic.action.create import related_create
from ckan.model import Related, Session, Package, repo, Group, Member
from ckan.lib.search import index_for
from pylons.i18n import gettext as _
import tieteet

TITLE_MATCH = re.compile(r'^(title_)?\d?$')


def package_show(context, data_dict):
    pkg_dict1 = ckan.logic.action.get.package_show(context, data_dict)
    pkg = Package.get(pkg_dict1['id'])
    if 'erelated' in pkg.extras:
        erelated = pkg.extras['erelated']
        if len(erelated):
            for value in erelated.split(';'):
                if len(Session.query(Related).filter(Related.title == value).all()) == 0:
                    data_dict = {'title': value,
                                 'type': _("Paper"),
                                 'dataset_id': pkg.id}
                    related_create(context, data_dict)
    if not pkg.title:
        for key in pkg.extras.keys():
            if TITLE_MATCH.match(key):
                repo.new_revision()
                pkg.title = pkg.extras[key]
                pkg.save()
                break
    context['extras_as_string'] = False
    pkg_dict = ckan.logic.action.get.package_show(context, data_dict)
    pkg_dict['private'] = False
    pkg_dict['owner_org'] = False
    pkg_dict['metadata_created'] = datetime.datetime.now().isoformat()
    pkg_dict['metadata_modified'] = datetime.datetime.now().isoformat()
    del pkg_dict['extras']['langtitles']
    del pkg_dict['extras']['events']
    del pkg_dict['extras']['orgauths']
    index = index_for('package')
    index.index_package(pkg_dict)
    return pkg_dict1
