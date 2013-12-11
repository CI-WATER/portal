import ckan.lib.base as base
import ckan.plugins as p
import logging
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.controllers import storage


tk = p.toolkit
_ = tk._  # translator function
log = logging.getLogger('ckan.logic')


class MockTranslator(object):
    def gettext(self, value):
        return value

    def ugettext(self, value):
        return value

    def ungettext(self, singular, plural, n):
        if n > 1:
            return plural
        return singular


class StringSettings(object):
    ckan_user_session_temp_dir = '/tmp/ckan'
    ueb_request_json_file_name = 'ueb_pkg_request.json'
    ueb_request_text_resource_file_name = 'ueb_pkg_request.txt'
    ueb_request_zip_file_name = 'ueb_request.zip'
    ueb_input_model_package_default_filename = 'ueb_model_pkg.zip'
    ueb_output_model_package_default_filename = 'ueb_model_output_pkg.zip'
    app_server_host_address = 'thredds-ci-water.bluezone.usu.edu'
    app_server_api_generate_ueb_package_url = '/api/GenerateUEBPackage'
    app_server_api_check_ueb_package_build_status = '/api/CheckUEBPackageBuildStatus'
    app_server_api_check_ueb_run_status_url = '/api/CheckUEBRunStatus'
    app_server_api_get_ueb_package_url = '/api/GetUEBPackage'
    app_server_api_run_ueb_url = '/api/RunUEB'
    app_server_api_get_ueb_run_output = '/api/UEBModelRunOutput'
    app_server_job_status_complete = 'Complete'
    app_server_job_status_processing = 'Processing'
    app_server_job_status_package_available = 'Package available'


def _register_translator():
    from paste.registry import Registry
    import pylons
    registry = Registry()
    registry.prepare()
    translator_obj = MockTranslator()
    registry.register(pylons.translator, translator_obj)

    
def update_resource(resource_id, data_dict, update_message=None, backgroundTask=False):
    """
    Updates a resource identified by resource_id
    with fields and corresponding values found in the data_dict
    Note: if key is not a field of the resource table in the data_dict
    that key/value pair will be added/updated to the 'extras' field of the resource

    param resource_id: id of the resource that needs update
    param data_dict: a dict object containing resource table field names
    as keys with corresponding values to be used for the update
    param update_message: message to be set for key 'message' in the context dict obj
    #A value for key 'message" in the context must be set to
    # avoid a bug in line#192 of the update.py under lib/action
    # without this, a TypeError will occur (TypeError:No object(name:translator) has been registered for this thread)
    """
    # TODO: this function needs throw exception if updating resource fails
    source = 'uebpackage.helpers.update_resource():'
    if backgroundTask:
        log.info(source + 'Register translator object for the background job')
        _register_translator()
        log.info(source + 'Translator object was registered for the background job')
        
    matching_resource = get_resource(resource_id)
    if not matching_resource:
        log.error(source + 'No resource was found for resource ID: %s' % resource_id)
        return None
        
    resource_update_action = tk.get_action('resource_update')
    context = {'model': base.model, 'session': base.model.Session}
    
    if update_message:
       context['message'] =  update_message
    
    try:
        context['user'] = tk.c.user or tk.c.author
    except:
        user = get_site_user()
        context['user'] = user.get('name')
        context['ignore_auth'] = True
    
    for key, value in data_dict.items():
        matching_resource[key] = value
    
    try:    
        updated_resource = resource_update_action(context, matching_resource)
    except Exception as e:
        log.error(source + 'Failed to update resource for resource ID: %s \nException %s' % (resource_id, e))
        updated_resource = None
            
    return updated_resource


def update_package(package_id, data_dict, update_message=None, backgroundTask=False):
    # TODO: this function needs throw exception if updating package fails

    source = 'uebpackage.helpers.update_package():'
    if backgroundTask:
        log.info(source + 'Register translator object for the background job')
        _register_translator()
        log.info(source + 'Translator object was registered for the background job')
        
    matching_package = get_package(package_id)
    if not matching_package:
        log.error(source + 'No dataset was found for dataset ID: %s' % package_id)
        return None
        
    package_update_action = tk.get_action('package_update')
    context = {'model': base.model, 'session': base.model.Session}
    
    if update_message:
       context['message'] =  update_message
    
    try:
        context['user'] = tk.c.user or tk.c.author
    except:
        user = get_site_user()
        context['user'] = user.get('name')
        context['ignore_auth'] = True
        pass
    
    if 'extras' in data_dict:
        pkg_extras = matching_package['extras']
        extras_to_update = data_dict['extras']
        for key, value in extras_to_update.items():
            for extra_item in pkg_extras:
                if extra_item['key'] == key:
                    extra_item['value'] = value
                        
    for key, value in data_dict.items():
        if key == 'extras':
            continue                        
        matching_package[key] = value
    
    try:    
        updated_package = package_update_action(context, matching_package)
    except Exception as e:
        log.error(source + 'Failed to update dataset for dataset ID: %s \nException %s' % (package_id, e))
        updated_package = None
        pass
            
    return updated_package


def get_package(pkg_id_or_name):  
    source = 'uebpackage.helpers.get_package():'
    package_show_action = tk.get_action('package_show')
    context = {'model': base.model, 'session': base.model.Session}
    
    # get the resource that has the id equal to the given resource id or name
    data_dict = {'id': pkg_id_or_name}
    try:
        matching_package_with_resources = package_show_action(context, data_dict)  
    except tk.ObjectNotFound:  # dataset does not exist or has been deleted
        log.error(source + 'No dataset was found for dataset ID: %s' % pkg_id_or_name)
        matching_package_with_resources = None
        pass
    
    return matching_package_with_resources


def get_package_for_resource(resource_id):
    context = {'model': base.model, 'session': base.model.Session}
    # get the matching resource object first
    resource_obj = base.model.Resource.get(resource_id)

    # get the package object that has the above resource
    related_pkg_obj = resource_obj.resource_group.package

    # convert the package object to dict
    package_dict = model_dictize.package_dictize(related_pkg_obj, context)

    return package_dict


def get_resource(resource_id):
    source = 'uebpackage.helpers.get_resource():'
    resource_show_action = tk.get_action('resource_show')
    context = {'model': base.model, 'session': base.model.Session}
    
    # get the resource that has the id equal to the given resource id
    data_dict = {'id': resource_id }
    try:
        matching_resource = resource_show_action(context, data_dict)
    except tk.ObjectNotFound: #resource does not exist or has been deleted
        log.error(source + 'No resource was found for resource ID: %s' % resource_id)
        matching_resource = None
        pass
    
    return matching_resource


def get_site_user():
    """
    Gets the default user that has admin lavel priviledges. User name for this
    default user comes from the CKAN ini file. This default user is used for
    authenticate backgound tasks that run outside the user session.
    """
    user = tk.get_action('get_site_user')(
            {'model': base.model, 'ignore_auth': True, 'defer_commit': True}, {}
            )
    return user


def retrieve_file_object_from_file_store(file_filestore_path): 
    """
    returns a file obj (in read mode) for the provided file in the ckan file store
    which the caller then can use to read the contents of the file (file_obj.read())
    param file_filestore_path : filecreationdatetime/followed by the filename
    """
    bucket_id = base.config.get('ckan.storage.bucket', 'default')   
    ofs = storage.get_ofs()
    file_obj = ofs.get_stream(bucket_id, file_filestore_path) 

    return file_obj