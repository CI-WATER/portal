from setuptools import setup, find_packages
<<<<<<< HEAD
import sys, os
=======
>>>>>>> remote_delineate/master

version = '0.1'

setup(
<<<<<<< HEAD
	name='ckanext-uebpackage',
	version=version,
	description="Extension to manage UEB package including UEB package creation",
=======
	name='ckanext-delineate',
	version=version,
	description="Watershed delineation extension",
>>>>>>> remote_delineate/master
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Pabitra Dash',
	author_email='pabitra.dash@usu.edu',
	url='',
<<<<<<< HEAD
	license='open source',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.uebpackage'],
=======
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.delineate'],
>>>>>>> remote_delineate/master
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
<<<<<<< HEAD
	entry_points=
	"""
    [ckan.plugins]
	# Add plugins here, eg	
	ueb_package =ckanext.uebpackage.plugin:UebPackagePlugins
	
	[ckan.celery_task]
	tasks = ckanext.uebpackage.celery_import:task_imports
=======
	entry_points=\
	"""
        [ckan.plugins]
	# Add plugins here, eg
	watershed_delineate=ckanext.delineate.plugin:DelineateWatershedPlugins
>>>>>>> remote_delineate/master
	""",
)
