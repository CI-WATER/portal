from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(
	name='ckanext-customdataset',
	version=version,
	description="This extension allows creation of different types of datasets with each type having unique set of metadata.",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='Pabitra Dash',
	author_email='pabitra.dash@usu.edu',
	url='',
	license='',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.customdataset'],
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
	# Add plugins here, eg
	ciwater_dataset_model_package=ckanext.customdataset.plugin:ModelPackagePlugin
    ciwater_dataset_multidimensional=ckanext.customdataset.plugin:MultidimensionalSpaceTimePlugin
    ciwater_dataset_geographic_feature_set=ckanext.customdataset.plugin:GeographicFeatureSetPlugin
    ciwater_dataset_geographic_raster=ckanext.customdataset.plugin:GeographicRasterPlugin
    ckan_dataset_type=ckanext.customdataset.plugin:DefaultDatasetPlugin
	""",
)
