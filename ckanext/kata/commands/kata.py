'''Paster commands'''

import sys

from ckan.lib.cli import CkanCommand
from ckan.lib.dictization.model_dictize import package_dictize
from ckanext.harvest.model import HarvestSource
from ckanext.kata.model import setup

class Kata(CkanCommand):
    '''
    Usage:

      katacmd initdb
        - Creates the necessary tables in the database
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
        elif cmd == 'sphinx':
            self.sphinx()
        elif cmd == 'crawl':
            self.generate_crawl()
        elif cmd == 'paituli_change':
            self.update_paituli()
        else:
            print 'Command %s not recognized' % cmd

    def _load_config(self):
        super(Kata, self)._load_config(load_site_user=False)

    def initdb(self):
        '''Database initialization'''
        setup()

    def harvest_sources(self):
        ddi = HarvestSource(url='http://www.fsd.uta.fi/fi/aineistot/luettelo/fsd-ddi-records-uris-fi.txt',
                            type='DDI')
        ddi.save()
        # oai = HarvestSource(url='http://helda.helsinki.fi/oai/request',
        #                    type='OAI-PMH')
        # oai.save()

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

    def update_paituli(self):
        import ckan.model as model
        from sqlalchemy import and_
        from sqlalchemy import update
        ses = model.Session
        ses.execute(update(model.Package).where(and_(model.Package.creator_user_id == '5f1f5463-6943-4610-968b-57a137e4e7f7',model.Package.name.like('urn-nbn-fi-csc-kata000010000%'))).values(creator_user_id = '5adaebc9-920f-4172-8f70-9797cf1c74ce'))
        ses.commit()