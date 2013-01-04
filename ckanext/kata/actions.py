import ckan.logic.action.get
from ckan.logic.action.create import related_create
from ckan.model import Related, Session, Package
from pylons.i18n import gettext as _


def package_show(context, data_dict):
    pkg_dict = ckan.logic.action.get.package_show(context, data_dict)
    pkg = Package.get(pkg_dict['id'])
    if 'erelated' in pkg.extras:
        erelated = pkg.extras['erelated']
        for value in erelated.split(';'):
            if len(Session.query(Related).filter(Related.title == value).all()) == 0:
                data_dict = {'title': value,
                             'type': _("Paper"),
                             'dataset_id': pkg_dict['id']}
                related_create(context, data_dict)
    return pkg_dict
