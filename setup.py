from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-kata',
	version=version,
	description="KATA extensions for CKAN",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Aleksi Suomalainen',
	author_email='aleksi.suomalainen@nomovok.com',
	url='https://github.com/kata-csc/ckanext-kata',
	license='AGPL',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.kata'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
	[ckan.plugins]
	# Add plugins here, eg
	kata=ckanext.kata.plugin:KataPlugin
	kata_metadata=ckanext.kata.plugin:KataMetadata
	""",
)
