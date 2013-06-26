'''Model classes for KATA
'''

from ckan.model.domain_object import DomainObject
from ckan.model import domain_object as domain_object
from ckan.model import meta, extension, core, user
from ckan import model as model
from sqlalchemy import types
import ckan.model.types as _types
from sqlalchemy.orm import mapper
from sqlalchemy import orm as orm
from sqlalchemy.schema import Table, Column, UniqueConstraint, ForeignKey
from sqlalchemy.engine.reflection import Inspector
import datetime
import vdm.sqlalchemy


class KataAccessRequest(DomainObject):
    def __init__(self, follower_id, object_id):
        self.user_id = follower_id
        self.pkg_id = object_id

    @classmethod
    def get(self, follower_id, object_id):
        '''Return a UserFollowingDataset object for the given follower_id and
        object_id, or None if no such follower exists.

        '''
        query = meta.Session.query(KataAccessRequest)
        query = query.filter(KataAccessRequest.user_id == follower_id)
        query = query.filter(KataAccessRequest.pkg_id == object_id)
        return query.first()

    @classmethod
    def is_requesting(cls, follower_id, object_id):
        '''Return True if follower_id is currently following object_id, False
        otherwise.

        '''
        return KataAccessRequest.get(follower_id, object_id) is not None

kata_access_request_table = Table('kata_req', meta.metadata,
    Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
    Column('pkg_id', types.UnicodeText, nullable=False),
    Column('user_id', types.UnicodeText, nullable=False),
    Column('created', types.DateTime, default=datetime.datetime.utcnow),
    UniqueConstraint('pkg_id', 'user_id', name='pkgusr_1'),
)

mapper(KataAccessRequest, kata_access_request_table, extension=[
                            extension.PluginMapperExtension(),
               ]
            )


user_extra_table = Table('user_extra', meta.metadata,
    Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
    Column('user_id', types.UnicodeText, ForeignKey('user.id')),
    Column('key', types.UnicodeText),
    Column('value', _types.JsonType),
)

vdm.sqlalchemy.make_table_stateful(user_extra_table)
user_extra_revision_table = core.make_revisioned_table(user_extra_table)


class UserExtra(vdm.sqlalchemy.RevisionedObjectMixin,
        vdm.sqlalchemy.StatefulObjectMixin,
        domain_object.DomainObject):
    pass

meta.mapper(UserExtra, user_extra_table, properties={
    'user': orm.relation(user.User,
        backref=orm.backref('_extras',
            collection_class=orm.collections.attribute_mapped_collection(u'key'),
            cascade='all, delete, delete-orphan',
            ),
        )
    },
    order_by=[user_extra_table.c.user_id, user_extra_table.c.key],
    extension=[vdm.sqlalchemy.Revisioner(user_extra_revision_table),],
)

vdm.sqlalchemy.modify_base_object_mapper(UserExtra, core.Revision, core.State)
UserExtraRevision = vdm.sqlalchemy.create_object_version(meta.mapper, UserExtra,
    user_extra_revision_table)

def _create_extra(key, value):
    return UserExtra(key=unicode(key), value=value)

_extras_active = vdm.sqlalchemy.stateful.DeferredProperty('_extras',
        vdm.sqlalchemy.stateful.StatefulDict, base_modifier=lambda x: x.get_as_of()) 
setattr(user.User, 'extras_active', _extras_active)
user.User.extras = vdm.sqlalchemy.stateful.OurAssociationProxy('extras_active', 'value',
            creator=_create_extra)

def setup():
    '''
    Creates the tables that are specified in this file
    '''
     
    if model.package_table.exists() and not kata_access_request_table.exists():
        kata_access_request_table.create()
    if model.user_table.exists() and not user_extra_table.exists() \
        and not user_extra_revision_table.exists():
        user_extra_table.create()
        user_extra_revision_table.create()

def drop_tables():
    if user_extra_revision_table.exists():
        user_extra_revision_table.drop()
    if user_extra_table.exists():
        user_extra_table.drop()
    if kata_access_request_table.exists():
        kata_access_request_table.drop()
