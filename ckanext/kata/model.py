'''Database model additions'''

import datetime
import logging

import sqlalchemy.orm as orm
from sqlalchemy.schema import Table, Column, UniqueConstraint, ForeignKey
import sqlalchemy.types as types
import vdm.sqlalchemy

import ckan.model as model
import ckan.model.domain_object as domain_object
from ckan.model import meta, extension, user
import ckan.model.types as _types

mapper = orm.mapper
log = logging.getLogger(__name__)


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
    if model.user_table.exists() and not user_extra_table.exists():
        user_extra_table.create()
        log.debug('User extra table created')


def delete_tables():
    '''
    Delete data from some extra tables to prevent IntegrityError between tests.
    '''
    #if user_extra_table.exists():
    #user_extra_table.delete()
    pass


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
