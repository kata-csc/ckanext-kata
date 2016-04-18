'''Setup Etsin'''

from setuptools import setup, find_packages

version = '3.1.0'

setup(
    name='ckanext-kata',
    version=version,
    description="KATA extension for CKAN",
    long_description="""Provides modified Add Dataset (package) page and other modifications. This extension contains also jQuery files, custom css (eg. kata.css) and several templates are overwritten from basic CKAN to provide the Kata/TTA looks.""",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='CSC - IT Center for Science Ltd.',
    author_email='kata-project@postit.csc.fi',
    url='https://github.com/kata-csc/ckanext-kata',
    license='AGPL',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.kata'],
    include_package_data=True,
    zip_safe=False,
    package_data={
        'ckan': [
            'i18n/*/LC_MESSAGES/*.mo',
        ]
    },
    install_requires=[
        'python-ldap == 2.4.16'
    ],
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),  #
            ('kata/theme/templates/package/**.html', 'ckan', None),
            ('kata/theme/templates/privacypolicy.html', 'ckan', None),
            ('kata/theme/templates/header.html', 'ckan', None),
            ('kata/theme/templates/footer.html', 'ckan', None),
            ('kata/theme/templates/kata/**.html', 'ckan', None),
            ('kata/theme/templates/group/**.html', 'ckan', None),
            ('kata/theme/templates/macros/**.html', 'ckan', None),
            ('kata/theme/templates/related/**.html', 'ckan', None),
            ('kata/theme/templates/revision/**.html', 'ckan', None),
            ('kata/theme/templates/contact/**.html', 'ckan', None),
            ('kata/theme/templates/snippets/**.html', 'ckan', None),
            ('kata/theme/templates/home/**.html', 'ckan', None),
            ('kata/theme/templates/user/**.html', 'ckan', None),
            ('kata/theme/templates/organization/**.html', 'ckan', None),
        ],
    },
    entry_points=
    """
    [ckan.plugins]
    # Add plugins here, eg
    kata=ckanext.kata.plugin:KataPlugin
    [paste.paster_command]
    katacmd = ckanext.kata.commands.kata:Kata
    """,

)
