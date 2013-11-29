# coding=utf-8
"""
Utility functions for Kata.
"""

from ckan.lib.email_notifications import send_notification
from pylons.i18n import _
from pylons import config
from ckan.model import User, Package
from ckan.lib import helpers as h
import logging
import tempfile
import subprocess
import urllib2
from lxml import etree
import socket
from ckanext.kata import settings

log = logging.getLogger(__name__)


def generate_pid():
    """ Generate dummy pid """
    import datetime
    return "urn:nbn:fi:csc-kata%s" % datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")


def send_email(req):
    """
    Send access request e-mail.
    """
    requester = User.get(req.user_id)
    pkg = Package.get(req.pkg_id)
    selrole = False
    for role in pkg.roles:
        if role.role == "admin":
            selrole = role
    if not selrole:
        return

    admin = User.get(selrole.user_id)
    admin_dict = admin.as_dict()
    admin_dict['name'] = admin.fullname if admin.fullname else admin.name
    
    msg = u'{a} ({b}) is requesting editing rights to dataset\n\n{c}\n\n\
for which you are currently an administrator. Please click this \
link if you want to allow this user to edit the metadata of the dataset:\n\
{d}\n\n{a} ({b}) pyytää muokkausoikeuksia tietoaineistoon\n\n{c}\n\n\
jonka ylläpitäjä olet. Klikkaa linkkiä, jos haluat tämän käyttäjän \
saavan muokkausoikeudet aineiston metatietoihin:\n\
{d}\n'

    controller = 'ckanext.kata.controllers:AccessRequestController'
    
    requester_name = requester.fullname if requester.fullname else requester.name
    accessurl = config.get('ckan.site_url', '') + h.url_for(controller=controller, action="unlock_access", id=req.id)
    body = msg.format(a=requester_name, b= requester.email, c=pkg.title if pkg.title else pkg.name, d=accessurl)
    email_dict = {}
    email_dict["subject"] = u"Access request for dataset / pyyntö koskien tietoaineistoa %s" % pkg.title if pkg.title else pkg.name
    email_dict["body"] = body
    send_notification(admin_dict, email_dict)


def convert_to_text(resource, resource_fname):
    """
    Convert structured documents to pure text.
    """
    fmt = resource.format.lower()
    prog = settings.TEXTOUTPUTPROGS[fmt] if (fmt in settings.TEXTOUTPUTPROGS and
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


def label_list_yso(tag_url):
    """
    Takes tag keyword URL and fetches the labels that link to it.
    """

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

