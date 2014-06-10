from setuptools import setup, find_packages

version = '0.1'

setup(
    name='ckanext-customization',
    version=version,
    description="This plugin customizes ckan instance to meet the needs of ciwater look and feel (theme).",
    long_description="""\
	""",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Pabitra Dash',
    author_email='pabitra.dash@usu.edu',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.customization'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points= \
        """
        [ckan.plugins]
	# Add plugins here, eg
	ciwater_customization=ckanext.customization.plugin:CustomizationPlugins
	""",
)
