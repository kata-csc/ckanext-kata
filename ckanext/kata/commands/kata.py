import sys
import datetime
from datetime import timedelta

from ckan.lib.cli import CkanCommand
from ckan.lib.dictization.model_dictize import package_dictize
import ckan.model as model
from ckanext.harvest.model import HarvestSource
from ckanext.kata.model import setup, KataAccessRequest
from ckanext.kata.utils import send_edit_access_request_email

class Kata(CkanCommand):
    '''
    Usage:

      katacmd initdb
        - Creates the necessary tables in the database
      katacmd send_request_emails
        - Sends edit request messages
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 6
    min_args = 0

    def __init__(self, name):
        super(Kata, self).__init__(name)

    def command(self):
        self._load_config()

        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]
        
        if cmd == 'initdb':
            self.initdb()
        elif cmd == 'harvest_sources':
            self.harvest_sources()
        elif cmd == 'send_request_emails':
            self.send_emails()
        elif cmd == 'sphinx':
            self.sphinx()
        elif cmd == 'crawl':
            self.generate_crawl()
        else:
            print 'Command %s not recognized' % cmd

    def _load_config(self):
        super(Kata, self)._load_config()

    def initdb(self):
#        kata = Group.get('KATA')
#        if not kata:
#            repo.new_revision()
#            kata = Group(name="KATA", title="Tieteenalat")
#            kata.save()
#            for tiede in tieteet.tieteet:
#                t = Group(description=tiede['description'],
#                          name=tiede['name'],
#                          title=tiede['title'])
#                t.save()
#                m = Member(group=kata, table_id=t.id, table_name="group")
#                m.save()
        setup()

    def harvest_sources(self):
        ddi = HarvestSource(url='http://www.fsd.uta.fi/fi/aineistot/luettelo/fsd-ddi-records-uris-fi.txt',
                            type='DDI')
        ddi.save()
        #oai = HarvestSource(url='http://helda.helsinki.fi/oai/request',
        #                    type='OAI-PMH')
        #oai.save()

    def sphinx(self):
        import sphinx
        from pkg_resources import load_entry_point
        cmd = load_entry_point('Sphinx', 'console_scripts', 'sphinx-build')
        cmd(['sphinx-build', '-b', 'html', '-d', self.args[1], self.args[2], self.args[3]])

    def generate_crawl(self):
        """
        Generate strings using packages for crawling.
        Example: sudo /opt/data/ckan/pyenv/bin/paster --plugin=ckanext-kata katacmd crawl -c /etc/kata.ini "http://10.10.10.10:5000/dataset/%(name)s.rdf"
        """
        if len(self.args) != 2:
            print "Crawl requires format argument"
            sys.exit(1)

        for package in model.Session.query(model.Package).all():
            print self.args[1] % package_dictize(package, {'model': model})
