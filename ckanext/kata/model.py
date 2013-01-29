'''Model classes for KATA
'''

from ckan.model.domain_object import DomainObject
from ckan.model import meta, extension, core
from ckan import model as model
from sqlalchemy import types
import ckan.model.types as _types
from sqlalchemy.orm import mapper
from sqlalchemy.schema import Table, Column, UniqueConstraint


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
    UniqueConstraint('pkg_id', 'user_id', name='pkgusr_1'),
)

mapper(KataAccessRequest, kata_access_request_table, extension=[
                            extension.PluginMapperExtension(),
               ]
            )


def setup():
    if model.package_table.exists():
        kata_access_request_table.create()
