from pylons import config
import ldap
import logging

log = logging.getLogger(__name__)

PASSWD = config.get('kata.ldap.password')
SERVER = config.get('kata.ldap.server')
DN = config.get('kata.ldap.dn')
BASEDN = config.get('kata.ldap.basedn')
BASEDN_PRJ = config.get('kata.ldap.basedn_prj')


def get_user_from_ldap(uploader):
    '''
    Tries to find the eppn from LDAP

    :param uploader: CSC user name
    :return: eppn
    '''
    if uploader:
        try:
            ld = ldap.initialize(SERVER)
            try:
                ld.simple_bind_s(DN, PASSWD)
                attrs = ['eduPersonPrincipalName']
                filtr = '(cn='+ uploader + ')'
                res = ld.search_s(BASEDN, ldap.SCOPE_SUBTREE, filtr, attrs)
                try:
                    if len(res) != 1:
                        return False
                    else:
                        return res[0][1]['eduPersonPrincipalName'][0]
                except Exception as e:
                    log.info('Faulty LDAP result %s' % e)
                    return False

            except ldap.INVALID_CREDENTIALS:
                log.info('Invalid credentials in LDAP call')
            except ldap.LDAPError, e:
                if type(e.message) == dict:
                    for (key, value) in e.message.iteritems():
                        print('%s: %s' % (key, value))
                else:
                    log.info(e.message)
        finally:
            ld.unbind()

    return False

def get_csc_project_from_ldap(project_id):
    '''
    Tries to find project entity from LDAP using project_id

    :param project_id: CSCPrjNum LDAP entity attribute value
    :return: distinguished name of the found project, or None if not found
    '''
    if project_id:
        try:
            ld = ldap.initialize(SERVER)
            try:
                ld.simple_bind_s(DN, PASSWD)
                attrs = ['dn']
                filtr = '(&(objectClass=CSCProject)(CSCPrjNum=' + project_id + '))'
                res = ld.search_s(BASEDN_PRJ, ldap.SCOPE_SUBTREE, filtr, attrs)
                try:
                    if len(res) != 1:
                        return None
                    else:
                        return res[0][0]
                except Exception as e:
                    log.warn('Faulty LDAP result %s' % e)
                    raise
            except ldap.INVALID_CREDENTIALS:
                log.warn('Invalid credentials in LDAP call')
                raise
            except ldap.LDAPError, e:
                if type(e.message) == dict:
                    for (key, value) in e.message.iteritems():
                        log.warn('{key}: {value}'.format(key=key, value=value))
                else:
                    log.warn(e.message)
                raise
        finally:
            ld.unbind()
    return None


def user_belongs_to_project_in_ldap(ldap_value, project_dn, use_eppn):
    '''
    Tries to resolve whether a user with specific email or eppn belongs
    to a specific project entity in LDAP

    :param project_dn: Project LDAP distinguished name
    :param use_eppn: if True, use eppn as ldap attribute, otherwise
     use mail as ldap attribute
    :return: True if user belongs to project, or False if not
    '''
    if ldap_value and project_dn:
        try:
            ld = ldap.initialize(SERVER)
            try:
                ld.simple_bind_s(DN, PASSWD)
                attrs = ['dn']
                if use_eppn:
                    filtr = '(&(memberof=' + project_dn + ')(eduPersonPrincipalName=' + ldap_value + '))'
                else:
                    filtr = '(&(memberof=' + project_dn + ')(mail=' + ldap_value + '))'
                res = ld.search_s(BASEDN, ldap.SCOPE_SUBTREE, filtr, attrs)
                if len(res) > 0:
                    return True
                return False
            except ldap.INVALID_CREDENTIALS:
                log.warn('Invalid credentials in LDAP call')
                raise
            except ldap.LDAPError, e:
                if type(e.message) == dict:
                    for (key, value) in e.message.iteritems():
                        log.warn('{key}: {value}'.format(key=key, value=value))
                else:
                    log.warn(e.message)
                raise
        finally:
            ld.unbind()
    return False