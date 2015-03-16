from pylons import config
import ldap
import logging

log = logging.getLogger(__name__)

PASSWD = config.get('kata.ldap.password')
SERVER = config.get('kata.ldap.server')
DN = config.get('kata.ldap.dn')
BASEDN = config.get('kata.ldap.basedn')


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

