from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-uebpackage',
	version=version,
	description="Extension to manage UEB package including UEB package creation",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Pabitra Dash',
	author_email='pabitra.dash@usu.edu',
	url='',
	license='open source',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.uebpackage'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=
	"""
    [ckan.plugins]
	# Add plugins here, eg	
	ueb_package =ckanext.uebpackage.plugin:UebPackagePlugins
	
	[ckan.celery_task]
	tasks = ckanext.uebpackage.celery_import:task_imports
	""",
)
