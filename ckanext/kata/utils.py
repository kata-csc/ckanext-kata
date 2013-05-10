from ckan.lib.email_notifications import send_notification
from pylons.i18n import gettext as _
from pylons import config
from ckan.model import User, Package
from ckan.lib import helpers as h
import logging
import tempfile
import subprocess
import urllib2
from lxml import etree
import socket

log = logging.getLogger(__name__)


def generate_pid():
    """ Generates dummy pid """
    import datetime
    return "urn:nbn:fi:csc-kata%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")


def send_email(req):
    requestee = User.get(req.user_id)
    pkg = Package.get(req.pkg_id)
    selrole = False
    for role in pkg.roles:
        if role.role == "admin":
            selrole = role
    if not selrole:
        return
    admin = User.get(selrole.user_id)
    msg = _("""%s (%s) is requesting editor access to a dataset you have created
    %s.

Please click this link if you want to give this user write access:
%s%s""")
    controller = 'ckanext.kata.controllers:AccessRequestController'
    body = msg % (requestee.name, requestee.email, pkg.title if pkg.title else pkg.name,
                config.get('ckan.site_url', ''),
                h.url_for(controller=controller,
                action="unlock_access",
                id=req.id))
    email_dict = {}
    email_dict["subject"] = _("Access request for dataset %s" % pkg.title if pkg.title else pkg.name)
    email_dict["body"] = body
    send_notification(admin.as_dict(), email_dict)

textoutputprogs = {
                   'doc': '/usr/bin/catdoc',
                   'html': '/usr/bin/w3m',
                   'odt': '/usr/bin/odt2txt',
                   'xls': '/usr/bin/xls2csv',
                   'ods': '/usr/bin/ods2txt',
                   'ppt': '/usr/bin/catppt',
                   'odp': '/usr/bin/odp2txt',
            }


def convert_to_text(resource, resource_fname):
    fmt = resource.format.lower()
    prog = textoutputprogs[fmt] if (fmt in textoutputprogs and \
                                    fmt is not 'txt') else ''
    if not prog:
        return None, None
    else:
        convert_fd, convert_path = tempfile.mkstemp()
        log.debug(resource_fname)
        p = subprocess.Popen([prog, resource_fname], stdout=convert_fd)
        p.communicate()
        return convert_fd, convert_path
    return None, None


def send_contact_email(owner, requestee, pkg, message):
    msg = _("""%s (%s) is requesting access to study material for dataset you have created
    %s.

The message is as follows:
%s
""")
    body = msg % (requestee.name,\
                  requestee.email,\
                  pkg.title if pkg.title else pkg.name,\
                  message)
    email_dict = {}
    email_dict["subject"] = _("Material access request for dataset %s" % pkg.title\
                              if pkg.title else pkg.name)
    email_dict["body"] = body
    send_notification(owner.as_dict(), email_dict)


# For use with label_list_yso.
_tagspaces = {
    'rdf' : 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'yso-meta' : 'http://www.yso.fi/onto/yso-meta/2007-03-02/',
    'rdfs' : "http://www.w3.org/2000/01/rdf-schema#",
    'ysa' : "http://www.yso.fi/onto/ysa/",
    'skos' : "http://www.w3.org/2004/02/skos/core#",
    'om' : "http://www.yso.fi/onto/yso-peilaus/2007-03-02/",
    'dc' : "http://purl.org/dc/elements/1.1/",
    'allars' : "http://www.yso.fi/onto/allars/",
    'daml' : "http://www.daml.org/2001/03/daml+oil#",
    'yso-kehitys' : "http://www.yso.fi/onto/yso-kehitys/",
    'owl' : "http://www.w3.org/2002/07/owl#",
    'xsd' : "http://www.w3.org/2001/XMLSchema#",
    'yso' : "http://www.yso.fi/onto/yso/",
}

def label_list_yso(tag_url):
    """
    Takes tag keyword URL and fetches the labels that link to it.
    """
    labels = []
    if not tag_url.endswith("?rdf=xml"):
        tag_url += "?rdf=xml" # Small necessary bit.
    request = urllib2.Request(tag_url, headers={"Accept":"application/rdf+xml"})
    try:
        contents = urllib2.urlopen(request).read()
    except (socket.error, urllib2.HTTPError, urllib2.URLError,):
        log.debug("Failed to read tag XML.")
        return []
    try:
        xml = etree.XML(contents)
    except etree.XMLSyntaxError:
        log.debug("Tag XMl syntax error.")
        return []
    for descr in xml.xpath('/rdf:RDF/rdf:Description', namespaces=_tagspaces):
        for tag in ('yso-meta:prefLabel', 'rdfs:label', 'yso-meta:altLabel',):
            nodes = descr.xpath('./%s' % tag, namespaces=_tagspaces)
            for node in nodes:
                t = node.text.strip() if node.text else ''
                if t:
                    labels.append(t)
    return labels

