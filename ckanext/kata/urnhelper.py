from lxml.etree import tostring
import datetime
from lxml.etree import Element, SubElement
from ckan.model import Package, Session
from ckan.lib import helpers
from pylons import config


class URNHelper(object):
    @classmethod
    def list_packages(cls):
        xmlns = "urn:nbn:se:uu:ub:epc-schema:rs-location-mapping"

        def locns(loc):
            return "{%s}%s" % (xmlns, loc)
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = "urn:nbn:se:uu:ub:epc-schema:rs-location-mapping http://urn.kb.se/resolve?urn=urn:nbn:se:uu:ub:epc-schema:rs-location-mapping&godirectly"
        records = Element("{" + xmlns + "}records",
                         attrib={"{" + xsi + "}schemaLocation": schemaLocation},
                         nsmap={'xsi': xsi, None: xmlns})
        q = Session.query(Package)
        q = q.filter(Package.name.ilike('urn:nbn:fi:csc-kata%'))
        pkgs = q.all()
        prot = SubElement(records, locns('protocol-version'))
        prot.text = '3.0'
        datestmp = SubElement(records, locns('datestamp'), attrib={'type': 'modified'})
        now = datetime.datetime.now().isoformat()
        datestmp.text = now
        for pkg in pkgs:
            record = SubElement(records, locns('record'))
            header = SubElement(record, locns('header'))
            datestmp = SubElement(header, locns('datestamp'), attrib={'type': 'modified'})
            datestmp.text = now
            identifier = SubElement(header, locns('identifier'))
            identifier.text = pkg.name
            destinations = SubElement(header, locns('destinations'))
            destination = SubElement(destinations, locns('destination'), attrib={'status': 'activated'})
            datestamp = SubElement(destination, locns('datestamp'), attrib={'type': 'activated'})
            url = SubElement(destination, locns('url'))
            url.text = "%s%s" % (config.get('ckan.site_url', ''),
                             helpers.url_for(controller='package',
                                       action='read',
                                       id=pkg.name))
        return tostring(records)

