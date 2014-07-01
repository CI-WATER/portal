__author__ = 'pabitra'
import ckan.plugins as p
import ckan.plugins.toolkit as tk
from ckan.logic.action.update import package_update
import validators as custom_owner_org_validator
from ckan.logic.validators import owner_org_validator as core_owner_org_validator

# ref: see this link below for explanation of validation functions
# http://pylonsbook.com/en/1.1/working-with-forms-and-validators.html
import formencode.validators as v
import logging
import os

log = logging.getLogger('ckan.logic')

dataset_type = None
_ = tk._  # translator function


def guess_package_type(expecting_name=False):
        """
            Guess the type of package from the URL handling the case
            where there is a prefix on the URL (such as /data/package)
        """

        # Special case: if the rot URL '/' has been redirected to the package
        # controller (e.g. by an IRoutes extension) then there's nothing to do
        # here.
        if tk.request.path == '/':
            return 'dataset'

        parts = [x for x in tk.request.path.split('/') if x]

        idx = -1
        if expecting_name:
            idx = -2

        pt = parts[idx]
        if pt == 'package':
            pt = 'dataset'

        return pt


def pkg_update(context, data_dict):

    # Here we are doing custom update for only 2 dataset types ('model-package' and 'model-configuration')
    # These 2 dataset types have metadata elements that are populated by the system only. That's why this custom
    # update is needed in order to be able to edit these 2 types of datasets as some of the metadata elements are not
    # exposed to the UI for user to update since there are supposed to be populated by the system.

    log.debug('my very own package_update() called')

    # get the already saved package
    orig_pkg = p.toolkit.get_action('package_show')(context, data_dict)

    # find the type pf package/dataset
    pkg_type = orig_pkg.get('type', None)
    if pkg_type is None:
        return package_update(context, data_dict)

    if pkg_type == 'model-package':
        if data_dict.get('package_run_status', None) is None:
            if orig_pkg.get('package_run_status', None):
                data_dict['package_run_status'] = orig_pkg['package_run_status']
            else:
                data_dict['package_run_status'] = 'Not yet submitted'

        if data_dict.get('package_run_job_id', None) is None:
            if orig_pkg.get('package_run_job_id', None):
                data_dict['package_run_job_id'] = orig_pkg['package_run_job_id']
            else:
                data_dict['package_run_job_id'] = ' '
    elif pkg_type == 'model-configuration':
        if data_dict.get('model_name', None) is None:
            data_dict['model_name'] = orig_pkg['model_name']

        if data_dict.get('processing_status', None) is None:
            data_dict['processing_status'] = orig_pkg['processing_status']

        if data_dict.get('package_build_request_job_id', None) is None:
            if orig_pkg.get('package_build_request_job_id', None):
                data_dict['package_build_request_job_id'] = orig_pkg['package_build_request_job_id']
            else:
                data_dict['package_build_request_job_id'] = ''

        if data_dict.get('package_availability', None) is None:
            if orig_pkg.get('package_availability', None):
                data_dict['package_availability'] = orig_pkg['package_availability']
            else:
                data_dict['package_availability'] = 'Not available'

    return package_update(context, data_dict)

def create_country_codes():
    '''Create country_codes vocab and tags, if they don't exist already.

    Note that you could also create the vocab and tags using CKAN's API,
    and once they are created you can edit them (e.g. to add and remove
    possible dataset country code values) using the API.

    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'country_codes'}
        tk.get_action('vocabulary_show')(context, data)
        logging.info("Example genre vocabulary already exists, skipping.")
    except tk.ObjectNotFound:
        logging.info("Creating vocab 'country_codes'")
        data = {'name': 'country_codes'}
        vocab = tk.get_action('vocabulary_create')(context, data)
        for tag in (u'uk', u'ie', u'de', u'fr', u'es'):
            logging.info(
                    "Adding tag {0} to vocab 'country_codes'".format(tag))
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tk.get_action('tag_create')(context, data)


def get_country_codes():
    '''Return the list of country codes from the country codes vocabulary.'''
    create_country_codes()
    try:
        country_codes = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'country_codes'})
        return country_codes
    except tk.ObjectNotFound:
        return None


def create_model_package_types():
    '''Create model_package_types vocab and tags, if they don't exist already.

    Note that you could also create the vocab and tags using CKAN's API,
    and once they are created you can edit them (e.g. to add and remove
    possible dataset country code values) using the API.

    '''
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'model_package_types'}
        tk.get_action('vocabulary_show')(context, data)
        logging.info("Example genre vocabulary already exists, skipping.")
    except tk.ObjectNotFound:
        logging.info("Creating vocab 'model_package_types'")
        data = {'name': 'model_package_types'}
        vocab = tk.get_action('vocabulary_create')(context, data)
        for tag in (u'Input', u'Complete'):
            logging.info(
                    "Adding tag {0} to vocab 'model_package_types'".format(tag))
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tk.get_action('tag_create')(context, data)


def get_model_package_types():
    '''Return the list of model package types from the model package types vocabulary.'''
    create_model_package_types()
    try:
        model_package_types = tk.get_action('tag_list')(
                data_dict={'vocabulary_id': 'model_package_types'})
        return model_package_types
    except tk.ObjectNotFound:
        return None


def get_dataset_type():
    global dataset_type
    return dataset_type


class _BaseDataset(tk.DefaultDatasetForm):
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    # Note: The IActions interface can be implemented only by
    # one subclass of this class
    p.implements(p.IActions, inherit=True)

    _instance = None
    _helpers_loaded = False
    _template_dir_added = False
    _route_mapped = False
    _resource_added = False

    @classmethod
    def _store_instance(cls, self):
        assert cls._instance is None
        cls._instance = self

    def _add_template_directory(self, config):
        if _BaseDataset._template_dir_added:
            return {}
        _BaseDataset._template_dir_added = True
        # Add this plugin's templates dir (ckanext-customdataset/ckanext/customdatset/templates)
        # to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')
        # add the extension's public dir path so that
        # ckan can find any resources used from this path
        # get the current dir path (here) for this plugin
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        our_public_dir = os.path.join(rootdir, 'ckanext', 'customdataset', 'public')
        config['extra_public_paths'] = ','.join([our_public_dir, config.get('extra_public_paths', '')])

    def _add_resource(self):
        if _BaseDataset._resource_added:
            return {}
        _BaseDataset._resource_added = True
        tk.add_resource('public', 'custom_dataset_resources')

    def update_config(self, config):
        self._store_instance(self)
        self._add_template_directory(config)
        self._add_resource()

    def before_map(self, map):
        if _BaseDataset._route_mapped:
            return map
        # Here create route shortcuts to all your extension's controllers and their actions
        map.connect('/dataset_types',
                    controller='ckanext.customdataset.controllers.datasettypes:DatasetTypesController',
                    action='select_dataset_types')
        _BaseDataset._route_mapped = True
        return map

    def get_helpers(self):
        return {'custom_dataset_type': get_dataset_type}

    def is_fallback(self):
        # Return False to register this plugin as the handler for
        # a specific package type.
        return False

    def new_template(self):
        return super(_BaseDataset, self).new_template()

    def read_template(self):
        return super(_BaseDataset, self).read_template()

    def edit_template(self):
        return super(_BaseDataset, self).edit_template()

    def search_template(self):
        return super(_BaseDataset, self).search_template()

    def history_template(self):
        return super(_BaseDataset, self).history_template()

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        ''' Update the facets_dict and return it. '''


        # We will actually remove all the core facets and add our own
        #facets_dict.clear()

        '''
        facets_dict['publisher_source_type'] = p.toolkit._('Source')
        facets_dict['secondary_publisher'] = p.toolkit._('Secondary Publisher')
        facets_dict['organization'] = p.toolkit._('Publisher')
        facets_dict['publisher_organization_type'] = p.toolkit._('Organisation Type')
        facets_dict['country'] = p.toolkit._('Recipient Country')
        facets_dict['filetype'] = p.toolkit._('File Type')
        if p.toolkit.c.userobj and p.toolkit.c.userobj.sysadmin:
            facets_dict['issue_type'] = p.toolkit._('Issue')

        '''

        return facets_dict

    # IPackageContoller
    def before_index(self, pkg_dict):
        '''
             Extensions will receive what will be given to the solr for
             indexing. This is essentially a flattened dict (except for
             multli-valued fields such as tags) of all the terms sent to
             the indexer. The extension can modify this by returning an
             altered version.
        '''
        pkg_dict['type'] = 'Dataset Types'
        return pkg_dict

    # IAction interface implementation
    def get_actions(self):
        log.debug('get_actions() called')
        return {
                 'package_update': pkg_update
        }

    def modify_schema(self, schema):
        _owner_org = custom_owner_org_validator.owner_org_validator
        if 'owner_org' in schema:
            schema['owner_org'] = [_owner_org if f is core_owner_org_validator else f for f in schema['owner_org']]

        return schema

# TODO: Made an attempt to implement all custom dataset types in one plugin
# From the tests, it seems it works for creating specific dataset type. However, it
# does not work for editing specific dataset
class CustomDatasetsPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    tk.add_resource('public', 'custom_dataset_resources')

    def update_config(self, config):
        # Add this plugin's templates dir (ckanext-customdataset/ckanext/customdatset/templates)
        # to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')
        # add the extension's public dir path so that
        # ckan can find any resources used from this path
        # get the current dir path (here) for this plugin
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        our_public_dir = os.path.join(rootdir, 'ckanext', 'customdataset', 'public')
        config['extra_public_paths'] = ','.join([our_public_dir, config.get('extra_public_paths', '')])

    def before_map(self, map):

        # Here create route shortcuts to all your extension's controllers and their actions
        map.connect('/dataset_types',
                    controller='ckanext.customdataset.controllers.datasettypes:DatasetTypesController',
                    action='select_dataset_types')

        return map

    def get_helpers(self):
        return {
                'custom_dataset_type': get_dataset_type,
                'model_package_types': get_model_package_types
               }

    def is_fallback(self):
        # Return False to register this plugin as the handler for
        # a specific package type.
        return False

    def package_types(self):
        # This plugin only handles the special custom package type (model-package), so it
        # registers itself as the handler for this specific package/dataset type.
        return ['model-package', 'multidimensional-space-time']

    def package_form(self):
        global dataset_type
        #dataset_type = self.package_types()[0]
        dataset_type = self._guess_package_type(True)
        return super(CustomDatasetsPlugin, self).package_form()

    def create_package_schema(self):
        schema = super(CustomDatasetsPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(CustomDatasetsPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(CustomDatasetsPlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add all custom metadata fields for this package/dataset type
        # make sure you specify the converter before you specify the validators for
        # each metadata elements. It looks like the validator needs to be always 'ignore-missing'
        # since this schema is used in dataset readonly mode
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_from_extras = tk.get_converter('convert_from_extras')
        if dataset_type == 'model-package':
            schema.update({
                    'pkg_model_name': [_convert_from_extras, _ignore_missing],
                    'model_version': [_convert_from_extras, _ignore_missing],
                    'north_extent': [_convert_from_extras, _ignore_missing],
                    'west_extent': [_convert_from_extras, _ignore_missing],
                    'south_extent': [_convert_from_extras, _ignore_missing],
                    'east_extent': [_convert_from_extras, _ignore_missing],
                    'simulation_start_day': [_convert_from_extras, _ignore_missing],
                    'simulation_end_day': [_convert_from_extras, _ignore_missing],
                    'time_step': [_convert_from_extras, _ignore_missing],
                    'package_type': [tk.get_converter('convert_from_tags')('model_package_types'), _ignore_missing],
                    'dataset_type': [_convert_from_extras, _ignore_missing]
                    })

        elif dataset_type == 'multidimensional-space-time':
            schema.update({
                    'variable_names': [_convert_from_extras, _ignore_missing],
                    'variable_units': [_convert_from_extras, _ignore_missing],
                    'north_extent': [_convert_from_extras, _ignore_missing],
                    'west_extent': [_convert_from_extras, _ignore_missing],
                    'south_extent': [_convert_from_extras, _ignore_missing],
                    'east_extent': [_convert_from_extras, _ignore_missing],
                    'data_start_day': [_convert_from_extras, _ignore_missing],
                    'data_end_day': [_convert_from_extras, _ignore_missing],
                    'projection': [_convert_from_extras, _ignore_missing],
                    'dataset_type': [_convert_from_extras, _ignore_missing]
                    })

        return schema

    def new_template(self):
        return super(CustomDatasetsPlugin, self).new_template()

    def read_template(self):
        return super(CustomDatasetsPlugin, self).read_template()

    def edit_template(self):
        return super(CustomDatasetsPlugin, self).edit_template()

    def search_template(self):
        return super(CustomDatasetsPlugin, self).search_template()

    def history_template(self):
        return super(CustomDatasetsPlugin, self).history_template()


    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        ''' Update the facets_dict and return it. '''


        # We will actually remove all the core facets and add our own
        #facets_dict.clear()

        '''
        facets_dict['publisher_source_type'] = p.toolkit._('Source')
        facets_dict['secondary_publisher'] = p.toolkit._('Secondary Publisher')
        facets_dict['organization'] = p.toolkit._('Publisher')
        facets_dict['publisher_organization_type'] = p.toolkit._('Organisation Type')
        facets_dict['country'] = p.toolkit._('Recipient Country')
        facets_dict['filetype'] = p.toolkit._('File Type')
        if p.toolkit.c.userobj and p.toolkit.c.userobj.sysadmin:
            facets_dict['issue_type'] = p.toolkit._('Issue')

        '''

        return facets_dict

    # implements IPackageController
    def before_index(self, data_dict):
        field_name = 'dataset_type'
        if data_dict.get('extras_{0}'.format(field_name)):
            if dataset_type == 'model-package':
                data_dict[field_name] = 'Model Package'
            elif dataset_type == 'multidimensional-space-time':
                data_dict[field_name] = 'Multidimensional Space Time'

        return data_dict

    def _guess_package_type(self, expecting_name=False):
        """
            Guess the type of package from the URL handling the case
            where there is a prefix on the URL (such as /data/package)
        """

        # Special case: if the rot URL '/' has been redirected to the package
        # controller (e.g. by an IRoutes extension) then there's nothing to do
        # here.
        if tk.request.path == '/':
            return 'dataset'

        parts = [x for x in tk.request.path.split('/') if x]

        idx = -1
        if expecting_name:
            idx = -2

        pt = parts[idx]
        if pt == 'package':
            pt = 'dataset'

        return pt

    def _modify_package_schema(self, schema):

        # TODO: need to implement chained validators
        # that allows to validate a group of fields together
        # e.g if start_date is entered then end_date is required

        # Add custom metadata fields to the schema, this one will use
        # convert_to_extras for all fields except for package_type for which convert_to_tags will be used.
        _not_empty = tk.get_validator('not_empty')
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_to_extras = tk.get_converter('convert_to_extras')

        if dataset_type == 'model-package':
            schema.update({
                    'pkg_model_name': [_not_empty, _convert_to_extras],
                    'model_version': [_not_empty, _convert_to_extras],
                    'north_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                    'west_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                    'south_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                    'east_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                    'simulation_start_day': [_ignore_missing, v.DateConverter(), _convert_to_extras],
                    'simulation_end_day': [_ignore_missing, v.DateConverter(), _convert_to_extras],
                    'time_step': [_ignore_missing, v.Number(), _convert_to_extras],
                    'package_type': [_not_empty, tk.get_converter('convert_to_tags')('model_package_types')],
                    'dataset_type': [_not_empty, _convert_to_extras]
                    })

        elif dataset_type == 'multidimensional-space-time':
            schema.update({
                    'variable_names': [_ignore_missing, _convert_to_extras],
                    'variable_units': [_ignore_missing, _convert_to_extras],
                    'north_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                    'west_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                    'south_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                    'east_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                    'data_start_day': [_ignore_missing, v.DateConverter(), _convert_to_extras],
                    'data_end_day': [_ignore_missing, v.DateConverter(), _convert_to_extras],
                    'projection': [_ignore_missing, _convert_to_extras],
                    'dataset_type': [_not_empty, _convert_to_extras]
                    })

        return schema


class DefaultDatasetPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    def is_fallback(self):
        # Return True to register this plugin as the handler for
        # a the CKAN default package type.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return ['dataset']

    def package_form(self):
        global dataset_type
        dataset_type = 'dataset'
        return super(DefaultDatasetPlugin, self).package_form()

    def create_package_schema(self):
        schema = super(DefaultDatasetPlugin, self).create_package_schema()
        schema = self._modify_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(DefaultDatasetPlugin, self).update_package_schema()
        schema = self._modify_schema(schema)
        return schema

    def dataset_facets(self, facets_dict, package_type):
        ''' Update the facets_dict and return it. '''

        # We will actually remove all the core facets and add our own
        #facets_dict.clear()
        facets_dict['dataset_type'] = p.toolkit._('Dataset Types')
        return facets_dict

    def before_search(self, search_params):
        '''
            Extensions will receive a dictionary with the query parameters,
            and should return a modified (or not) version of it.

            search_params will include an `extras` dictionary with all values
            from fields starting with `ext_`, so extensions can receive user
            input from specific fields.

        '''
        return search_params

    # implements IPackageController
    def before_view(self, pkg_dict):
        '''
             Extensions will recieve this before the dataset gets
             displayed. The dictionary passed will be the one that gets
             sent to the template.
        '''
        return pkg_dict

    # implements IMapper
    '''
    def before_insert(self, mapper, connection, instance):
        """
        Receive an object instance before that instance is INSERTed into
        its table.
        """
        my_instance = instance
    '''

    def _modify_schema(self, schema):
        _owner_org = custom_owner_org_validator.owner_org_validator
        if 'owner_org' in schema:
            schema['owner_org'] = [_owner_org if f is core_owner_org_validator else f for f in schema['owner_org']]
        return schema

class ModelPackagePlugin(p.SingletonPlugin, _BaseDataset):
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.ITemplateHelpers, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IPackageController, inherit=True)

    # Note: only one subclass of the _BaseDataset class can implement the IActions interface
    # Therefore, we are not using the following statement in other dataset types that inherit
    # from _BaseDataset class
    p.implements(p.IActions, inherit=True)

    def get_helpers(self):
        helpers = super(ModelPackagePlugin, self).get_helpers()
        helpers['model_package_types'] = get_model_package_types
        return helpers

    def package_types(self):
        # This plugin only handles the special custom package type (model-package), so it
        # registers itself as the handler for this specific package/dataset type.
        return ['model-package']

    def _modify_package_schema(self, schema):

        # TODO: need to implement chained validators
        # that allows to validate a group of fields together
        # e.g if start_date is entered then end_date is required

        # Add custom metadata fields to the schema, this one will use
        # convert_to_extras for all fields except for package_type for which convert_to_tags will be used.
        _not_empty = tk.get_validator('not_empty')
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_to_extras = tk.get_converter('convert_to_extras')

        schema.update({
                'pkg_model_name': [_not_empty, _convert_to_extras],
                'model_version': [_not_empty, _convert_to_extras],
                'north_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'west_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'south_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'east_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'simulation_start_day': [_ignore_missing, v.DateConverter(), _convert_to_extras],
                'simulation_end_day': [_ignore_missing, v.DateConverter(), _convert_to_extras],
                'time_step': [_ignore_missing, v.Number(), _convert_to_extras],
                'package_type': [_not_empty, tk.get_converter('convert_to_tags')('model_package_types')],
                'package_run_status': [_ignore_missing, _convert_to_extras],
                'package_run_job_id': [_ignore_missing, _convert_to_extras],
                'dataset_type': [_not_empty, _convert_to_extras]
                })

        schema = super(ModelPackagePlugin, self).modify_schema(schema)
        return schema

    def create_package_schema(self):
        create_model_package_types()
        schema = super(ModelPackagePlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(ModelPackagePlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(ModelPackagePlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add all custom metadata fields for this package/dataset type
        # make sure you specify the converter before you specify the validators for
        # each metadata elements. It looks like the validator needs to be always 'ignore-missing'
        # since this schema is used in dataset readonly mode
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_from_extras = tk.get_converter('convert_from_extras')

        schema.update({
                'pkg_model_name': [_convert_from_extras, _ignore_missing],
                'model_version': [_convert_from_extras, _ignore_missing],
                'north_extent': [_convert_from_extras, _ignore_missing],
                'west_extent': [_convert_from_extras, _ignore_missing],
                'south_extent': [_convert_from_extras, _ignore_missing],
                'east_extent': [_convert_from_extras, _ignore_missing],
                'simulation_start_day': [_convert_from_extras, _ignore_missing],
                'simulation_end_day': [_convert_from_extras, _ignore_missing],
                'time_step': [_convert_from_extras, _ignore_missing],
                'package_type': [tk.get_converter('convert_from_tags')('model_package_types'), _ignore_missing],
                'package_run_status': [_convert_from_extras, _ignore_missing],
                'package_run_job_id': [_convert_from_extras, _ignore_missing],
                'dataset_type': [_convert_from_extras, _ignore_missing]
                })

        return schema

    def package_form(self):
        global dataset_type
        dataset_type = 'model-package'
        return super(ModelPackagePlugin, self).package_form()

    # implements IPackageController
    def before_index(self, data_dict):
        field_name = 'dataset_type'
        if data_dict.get('extras_{0}'.format(field_name)):
                data_dict[field_name] = 'Model Package'

        return data_dict

    # IAction interface implementation
    # def get_actions(self):
    #     return super(ModelPackagePlugin, self).get_actions()

class MultidimensionalSpaceTimePlugin(p.SingletonPlugin, _BaseDataset):
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    #p.implements(p.ITemplateHelpers, inherit=True)

    def package_types(self):
        # This plugin only handles the special custom package type (model-package), so it
        # registers itself as the handler for this specific package/dataset type.
        return ['multidimensional-space-time']

    def _modify_package_schema(self, schema):

        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_to_extras = tk.get_converter('convert_to_extras')
        _not_empty = tk.get_validator('not_empty')

        # Add custom metadata fields to the schema, this one will use
        # convert_to_extras for all fields.
        schema.update({
                'variable_names': [_ignore_missing, _convert_to_extras],
                'variable_units': [_ignore_missing, _convert_to_extras],
                'north_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'west_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'south_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'east_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'data_start_day': [_ignore_missing, v.DateConverter(), _convert_to_extras],
                'data_end_day': [_ignore_missing, v.DateConverter(), _convert_to_extras],
                'projection': [_ignore_missing, _convert_to_extras],
                'dataset_type': [_not_empty, _convert_to_extras]
                })

        schema = super(MultidimensionalSpaceTimePlugin, self).modify_schema(schema)
        return schema

    def create_package_schema(self):
        schema = super(MultidimensionalSpaceTimePlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(MultidimensionalSpaceTimePlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(MultidimensionalSpaceTimePlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add all custom metadata fields for this package/dataset type
        # make sure you specify the converter before you specify the validators for
        # each metadata elements. It looks like the validator needs to be always 'ignore-missing'
        # since this schema is used in dataset readonly mode
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_from_extras = tk.get_converter('convert_from_extras')

        schema.update({
                'variable_names': [_convert_from_extras, _ignore_missing],
                'variable_units': [_convert_from_extras, _ignore_missing],
                'north_extent': [_convert_from_extras, _ignore_missing],
                'west_extent': [_convert_from_extras, _ignore_missing],
                'south_extent': [_convert_from_extras, _ignore_missing],
                'east_extent': [_convert_from_extras, _ignore_missing],
                'data_start_day': [_convert_from_extras, _ignore_missing],
                'data_end_day': [_convert_from_extras, _ignore_missing],
                'projection': [_convert_from_extras, _ignore_missing],
                'dataset_type': [_convert_from_extras, _ignore_missing]
                })

        return schema

    def package_form(self):
        global dataset_type
        dataset_type = self.package_types()[0]
        dataset_type = guess_package_type(True)
        return super(MultidimensionalSpaceTimePlugin, self).package_form()


class GeographicRasterPlugin(p.SingletonPlugin, _BaseDataset):
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    #p.implements(p.ITemplateHelpers, inherit=True)

    def package_types(self):
        # This plugin only handles the special custom package type (geographic-raster), so it
        # registers itself as the handler for this specific package/dataset type.
        return ['geographic-raster']

    def _modify_package_schema(self, schema):

        # Add custom metadata fields to the schema, this one will use
        # convert_to_extras for all fields.
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_to_extras = tk.get_converter('convert_to_extras')
        _not_empty = tk.get_validator('not_empty')

        schema.update({
                'variable_names': [_ignore_missing, _convert_to_extras],
                'variable_units': [_ignore_missing, _convert_to_extras],
                'north_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'west_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'south_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'east_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'cell_size': [_ignore_missing, v.Number(), _convert_to_extras],
                'projection': [_ignore_missing, _convert_to_extras],
                'dataset_type': [_not_empty, _convert_to_extras]
                })

        schema = super(GeographicRasterPlugin, self).modify_schema(schema)
        return schema

    def create_package_schema(self):
        schema = super(GeographicRasterPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(GeographicRasterPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(GeographicRasterPlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add all custom metadata fields for this package/dataset type
        # make sure you specify the converter before you specify the validators for
        # each metadata elements. It looks like the validator needs to be always 'ignore-missing'
        # since this schema is used in dataset readonly mode
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_from_extras = tk.get_converter('convert_from_extras')

        schema.update({
                'variable_names': [_convert_from_extras, _ignore_missing],
                'variable_units': [_convert_from_extras, _ignore_missing],
                'north_extent': [_convert_from_extras, _ignore_missing],
                'west_extent': [_convert_from_extras, _ignore_missing],
                'south_extent': [_convert_from_extras, _ignore_missing],
                'east_extent': [_convert_from_extras, _ignore_missing],
                'cell_size': [_convert_from_extras, _ignore_missing],
                'projection': [_convert_from_extras, _ignore_missing],
                'dataset_type': [_convert_from_extras, _ignore_missing]
                })

        return schema

    def package_form(self):
        global dataset_type
        dataset_type = self.package_types()[0]
        return super(GeographicRasterPlugin, self).package_form()


class GeographicFeatureSetPlugin(p.SingletonPlugin, _BaseDataset):
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    #p.implements(p.ITemplateHelpers, inherit=True)

    def package_types(self):
        # This plugin only handles the special custom package type (geographic-feature-set), so it
        # registers itself as the handler for this specific package/dataset type.
        return ['geographic-feature-set']

    def _modify_package_schema(self, schema):

        # Add custom metadata fields to the schema, this one will use
        # convert_to_extras for all fields.
        _convert_to_extras = tk.get_converter('convert_to_extras')
        _not_empty = tk.get_validator('not_empty')
        _ignore_missing = tk.get_validator('ignore_missing')

        schema.update({
                'variable_name': [_ignore_missing, _convert_to_extras],
                'variable_unit': [_ignore_missing, _convert_to_extras],
                'north_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'west_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'south_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'east_extent': [_ignore_missing, v.Number(), _convert_to_extras],
                'projection': [_ignore_missing, _convert_to_extras],
                'dataset_type': [_not_empty, _convert_to_extras]
                })
        schema = super(GeographicFeatureSetPlugin, self).modify_schema(schema)
        return schema

    def create_package_schema(self):
        schema = super(GeographicFeatureSetPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(GeographicFeatureSetPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(GeographicFeatureSetPlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add all custom metadata fields for this package/dataset type
        # make sure you specify the converter before you specify the validators for
        # each metadata elements. It looks like the validator needs to be always 'ignore-missing'
        # since this schema is used in dataset readonly mode
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_from_extras = tk.get_converter('convert_from_extras')

        schema.update({
                'variable_name': [_convert_from_extras, _ignore_missing],
                'variable_unit': [_convert_from_extras, _ignore_missing],
                'north_extent': [_convert_from_extras, _ignore_missing],
                'west_extent': [_convert_from_extras, _ignore_missing],
                'south_extent': [_convert_from_extras, _ignore_missing],
                'east_extent': [_convert_from_extras, _ignore_missing],
                'projection': [_convert_from_extras, _ignore_missing],
                'dataset_type': [_convert_from_extras, _ignore_missing]
                })

        return schema

    def package_form(self):
        global dataset_type
        dataset_type = self.package_types()[0]
        return super(GeographicFeatureSetPlugin, self).package_form()


class ModelConfigurationPlugin(p.SingletonPlugin, _BaseDataset):
    p.implements(p.IDatasetForm, inherit=True)
    p.implements(p.IConfigurer, inherit=True)
    p.implements(p.IRoutes, inherit=True)
    #p.implements(p.IActions, inherit=True)

    def package_types(self):
        # This plugin only handles the special custom package type (model-configuration), so it
        # registers itself as the handler for this specific package/dataset type.
        return ['model-configuration']

    def _modify_package_schema(self, schema):

        # Add custom metadata fields to the schema, this one will use
        # convert_to_extras for all fields.
        _convert_to_extras = tk.get_converter('convert_to_extras')
        _not_empty = tk.get_validator('not_empty')
        _ignore_missing = tk.get_validator('ignore_missing')

        schema.update({
                'model_name': [_not_empty, _convert_to_extras],
                'processing_status': [_not_empty, _convert_to_extras],
                'package_build_request_job_id': [_ignore_missing, _convert_to_extras],
                'package_availability': [_ignore_missing, _convert_to_extras]
                })

        schema = super(ModelConfigurationPlugin, self).modify_schema(schema)
        return schema

    def create_package_schema(self):
        schema = super(ModelConfigurationPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(ModelConfigurationPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def show_package_schema(self):
        schema = super(ModelConfigurationPlugin, self).show_package_schema()

        # Don't show vocab tags mixed in with normal 'free' tags
        # (e.g. on dataset pages, or on the search page)
        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))

        # Add all custom metadata fields for this package/dataset type
        # make sure you specify the converter before you specify the validators for
        # each metadata elements. It looks like the validator needs to be always 'ignore-missing'
        # since this schema is used in dataset readonly mode
        _ignore_missing = tk.get_validator('ignore_missing')
        _convert_from_extras = tk.get_converter('convert_from_extras')

        schema.update({
                'model_name': [_convert_from_extras, _ignore_missing],
                'processing_status': [_convert_from_extras, _ignore_missing],
                'package_build_request_job_id': [_convert_from_extras, _ignore_missing],
                'package_availability': [_convert_from_extras, _ignore_missing]
                })

        return schema

    def package_form(self):
        global dataset_type
        dataset_type = self.package_types()[0]
        return super(ModelConfigurationPlugin, self).package_form()

