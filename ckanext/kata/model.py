'''Database model additions for Kata'''

import datetime
import logging

import sqlalchemy.orm as orm
from sqlalchemy.schema import Table, Column, UniqueConstraint, ForeignKey
import sqlalchemy.types as types
import vdm.sqlalchemy

import ckan.model as model
from ckan.model.domain_object import DomainObject
import ckan.model.domain_object as domain_object
from ckan.model import meta, extension, user
import ckan.model.types as _types

mapper = orm.mapper
log = logging.getLogger(__name__)


class KataAccessRequest(DomainObject):
    '''
    Class for edit access requests.
    '''

    def __init__(self, follower_id, object_id):
        self.user_id = follower_id
        self.pkg_id = object_id

    @classmethod
    def get(cls, follower_id, object_id):
        '''
        Return a `UserFollowingDataset` object for the given `follower_id` and
        `object_id`, or None if no such follower exists.
        '''
        query = meta.Session.query(KataAccessRequest)
        query = query.filter(KataAccessRequest.user_id == follower_id)
        query = query.filter(KataAccessRequest.pkg_id == object_id)
        return query.first()

    @classmethod
    def is_requesting(cls, follower_id, object_id):
        '''
        Return `True` if `follower_id` is currently following `object_id`, `False`
        otherwise.
        '''
        return KataAccessRequest.get(follower_id, object_id) is not None


class UserExtra(vdm.sqlalchemy.RevisionedObjectMixin,
                vdm.sqlalchemy.StatefulObjectMixin,
                domain_object.DomainObject):
    '''
    Class for extra user profile info.
    '''

    @classmethod
    def by_userid(cls, userid):
        '''
        Return all user extra records belonging to User 'userid'.
        '''
        session_query = meta.Session.query(cls).autoflush(False)
        return session_query.filter_by(user_id=userid).all()

    @classmethod
    def by_userid_key(cls, userid, key):
        '''
        Return all user extra records belonging to User `userid` with `key=key`.
        '''
        session_query = meta.Session.query(cls).autoflush(False)
        return session_query.filter_by(user_id=userid).filter_by(key=key).first()

    def get_user(self):
        return self.user


def _create_extra(key, value):
    '''
    Create a UserExtra instance.
    '''
    return UserExtra(key=unicode(key), value=value)


def setup():
    '''
    Creates the tables that are specified in this file
    '''
    if model.package_table.exists() and not kata_access_request_table.exists():
        kata_access_request_table.create()
        log.debug('Kata access request table created')

    if model.user_table.exists() and not user_extra_table.exists():
        user_extra_table.create()
        log.debug('User extra table created')


def delete_tables():
    '''
    Delete data from some extra tables to prevent IntegrityError between tests.
    '''

    #if user_extra_table.exists():
    #user_extra_table.delete()
    if kata_access_request_table.exists():
        kata_access_request_table.delete()


kata_access_request_table = Table('kata_req', meta.metadata,
                                  Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                                  Column('pkg_id', types.UnicodeText, nullable=False),
                                  Column('user_id', types.UnicodeText, nullable=False),
                                  Column('created', types.DateTime, default=datetime.datetime.utcnow),
                                  UniqueConstraint('pkg_id', 'user_id', name='pkgusr_1'),
                                  )

mapper(KataAccessRequest, kata_access_request_table, extension=[
    extension.PluginMapperExtension(),
    ])


user_extra_table = Table('user_extra', meta.metadata,
                         Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                         Column('user_id', types.UnicodeText, ForeignKey('user.id')),
                         Column('key', types.UnicodeText),
                         Column('value', _types.JsonType),
                         )
vdm.sqlalchemy.make_table_stateful(user_extra_table)

meta.mapper(UserExtra, user_extra_table, properties={
    'user': orm.relation(user.User,
                         backref=orm.backref('_extras',
                                             collection_class=orm.collections.attribute_mapped_collection(u'key'),
                                             cascade='all, delete, delete-orphan',
                                             ),
                         )
},
            order_by=[user_extra_table.c.user_id, user_extra_table.c.key],
            )

extras_active = vdm.sqlalchemy.stateful.DeferredProperty('_extras',
                                                          vdm.sqlalchemy.stateful.StatefulDict,
                                                          base_modifier=lambda x: x.get_as_of())
setattr(user.User, 'extras_active', extras_active)
user.User.extras = vdm.sqlalchemy.stateful.OurAssociationProxy('extras_active', 'value', creator=_create_extra)
