'''Paster commands'''

from ckan.lib.cli import CkanCommand
import sys

class Hierarchy(CkanCommand):
    '''
    Usage:

    hierarchy create codes.csv
        - Creates a new organization hierarchy based on the given csv file.
    hierarchy purge
        - Removes (hide) all empty organizations that do not have any datasets
          associated from the database
    '''

    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 4
    min_args = 1

    def __init__(self, name):
        super(Hierarchy, self).__init__(name)

    def command(self):
        #self._load_config()

        if len(self.args) == 0:
            self.parser.print_usage()
            sys.exit(1)
        cmd = self.args[0]

        if cmd == 'create':
            self.create()
        elif cmd == 'purge':
            confirmation = raw_input("Are you sure you want to delete all empty organizations? (y/n)\n>> ")
            if confirmation.lower() in ['y', 'yes']:
                self.purge()
            else:
                print "Exiting script."
                sys.exit(1)
        else:
            print 'Command %s not recognized' % cmd

    def _load_config(self):
        super(Hierarchy, self)._load_config(load_site_user=False)

    def create(self):
        print "Hello World! (create)"

    def purge(self):
        print "Hello World! (purge)"