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


def resource_to_dataset(data_dict):
    '''
    Move some fields from resources to dataset. Used for viewing a dataset.
    '''
    # TODO: Use converters and show_package_schema instead.

    try:
        # UI can't handle multiple instances of a dataset, so now use only the first.
        resource = [res for res in data_dict['resources'] if res['resource_type'] == settings.RESOURCE_TYPE_DATASET ][0]
    except (KeyError, IndexError):
        log.debug('Dataset without a dataset resource: %s' % data_dict['id'])
        return data_dict

    if resource:
        data_dict.update({
            'direct_download_url' : resource.get('url'),
            'checksum' : resource.get('hash'),
            'mimetype' : resource.get('mimetype'),
            'algorithm' : resource.get('algorithm'),
        })

    return data_dict


def dataset_to_resource(data_dict):
    '''
    Move some fields from dataset to resources. Used for saving to DB.
    '''
    # TODO: Use converters and create_package_schema instead.

    if 'resources' not in data_dict:
        data_dict['resources'] = []

    data_dict['resources'].append({
        #'package_id' : pkg_dict1['id'],
        'url' : data_dict.pop('direct_download_url', settings.DATASET_URL_UNKNOWN),
        'hash' : data_dict.pop('checksum', u''),
        'mimetype' : data_dict.pop('mimetype', u''),
        'algorithm' : data_dict.pop('algorithm', u''),
        'resource_type' : settings.RESOURCE_TYPE_DATASET,
    })

    return data_dict
