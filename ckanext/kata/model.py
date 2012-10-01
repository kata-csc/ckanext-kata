'''Model classes for KATA
'''

from ckan.model.domain_object import DomainObject
from ckan.model import meta, extension, core
from sqlalchemy import types
from sqlalchemy.orm import mapper
from sqlalchemy.schema import Table, Column, ForeignKey

import vdm.sqlalchemy

class KataContact(DomainObject):
    pass

kata_contact_table = Table('kata_contact', meta.metadata,
                           Column('package_id', types.UnicodeText, ForeignKey('package.id')),
                           Column('role', types.Integer),
                           Column('name', types.UnicodeText),
                           Column('phone', types.UnicodeText),
                           Column('address', types.UnicodeText),
                           )

vdm.sqlalchemy.make_table_stateful(kata_contact_table)
kata_contact_revision_table = core.make_revisioned_table(kata_contact_table)
mapper(KataContact, kata_contact_table, extension=[
                            vdm.sqlalchemy.Revisioner(kata_contact_revision_table),
                            extension.PluginMapperExtension(),
               ]
            )

class MetadataModel(DomainObject):
    pass

metadata_table = Table('kata_metadata', meta.metadata,
                    Column('metadata_id', types.UnicodeText, primary_key=True),
                    Column('metadata_modified', types.UnicodeText),
                    Column('package_id', types.UnicodeText, ForeignKey('package.id')),
                       )

vdm.sqlalchemy.make_table_stateful(metadata_table)
metadata_revision_table = core.make_revisioned_table(metadata_table)
mapper(MetadataModel, metadata_table, extension=[
                            vdm.sqlalchemy.Revisioner(metadata_revision_table),
                            extension.PluginMapperExtension(),
               ]
            )

vdm.sqlalchemy.modify_base_object_mapper(MetadataModel,
                                         core.Revision,
                                         core.State)
MetadataRevision = vdm.sqlalchemy.create_object_version(meta.mapper,
                                                    MetadataModel,
                                                    metadata_revision_table)


def setup():
    if model.package_table.exists():
        kata_contact_table.create()

        log.debug('Kata tables created')