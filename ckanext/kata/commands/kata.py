import sys
import re
from pprint import pprint

from ckan import model
from ckan.model import Group, repo, Member
from ckan.logic import get_action, ValidationError

from ckan.lib.cli import CkanCommand
import ckanext.kata.tieteet as tieteet
from ckanext.harvest.model import HarvestSource

class Kata(CkanCommand):
    '''
    Usage:

      kata initdb
        - Creates the necessary tables in the database
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 6
    min_args = 0

    def __init__(self,name):

        super(Kata,self).__init__(name)

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
        else:
            print 'Command %s not recognized' % cmd

    def _load_config(self):
        super(Kata, self)._load_config()

    def initdb(self):
        kata = Group.get('KATA')
        if not kata:
            repo.new_revision()
            kata = Group(name="KATA", title="Tieteenalat")
            kata.save()
            for tiede in tieteet.tieteet:
                t = Group(description=tiede['description'],
                          name=tiede['name'],
                          title=tiede['title'])
                t.save()
                m = Member(group=kata, table_id=t.id, table_name="group")
                m.save()

    def harvest_sources(self):
        ddi = HarvestSource(url='http://www.fsd.uta.fi/fi/aineistot/luettelo/fsd-ddi-records-uris-fi.txt',
                            type='DDI')
        ddi.save()
        oai = HarvestSource(url='http://helda.helsinki.fi/oai/request',
                            type='OAI-PMH')
        oai.save()
