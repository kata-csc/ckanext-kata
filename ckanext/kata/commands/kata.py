import sys
import re
from pprint import pprint

from ckan import model
from ckan.logic import get_action, ValidationError

from ckan.lib.cli import CkanCommand

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
        else:
            print 'Command %s not recognized' % cmd

    def _load_config(self):
        super(Kata, self)._load_config()

    def initdb(self):
        from ckanext.kata.model import setup as db_setup
        db_setup()
