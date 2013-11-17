from ckan.lib.celery_app import celery
import ckan.lib.base as base
import ckan.plugins.toolkit as tk
from ckan.controllers import storage
import httplib
import os
from datetime import datetime
import helpers as uebhelper
import logging

_ = tk._  # translator function

log = logging.getLogger('ckan.logic')

service_host_address = 'thredds-ci-water.bluezone.usu.edu'

@celery.task
def add(x, y):
    return x + y    

@celery.task
def check_ueb_request_process_status():
    source = 'uebpackage.tasks.check_ueb_request_process_status():'
    global service_host_address
    service_request_api_url = '/api/CheckUEBPackageBuildStatus'
    connection = httplib.HTTPConnection(service_host_address)
    request_resources_with_status_processing = _get_ueb_pkg_request_resources_by_processing_status('Processing')
    if len(request_resources_with_status_processing) == 0:
        log.info(source + "No UEB model package build request has a status of 'Processing' at this time")
        
    for resource in request_resources_with_status_processing:
        pkg_process_job_id = resource['PackageProcessJobID']
        resource_id = resource['id']
        service_request_url = service_request_api_url + '?packageID=' + pkg_process_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()
        
        if service_call_results.status == httplib.OK:
            request_processing_status = service_call_results.read()
            log.info(source + 'UEB model package build status as returned from App server '
                              'for PackageJobID:%s is %s' % (pkg_process_job_id, request_processing_status))
        else:
            request_processing_status = "Error"
            log.error(source + 'HTTP status %d returned from App server when checking '
                               'status for PackageJobID:%s' % (service_call_results.status, pkg_process_job_id))
        
        connection.close()
        
        # update the resource processing status
        _update_ueb_request_process_status(resource_id, request_processing_status)        


def check_ueb_run_status():
    source = 'uebpackage.tasks.check_ueb_run_status():'
    global service_host_address
    service_request_api_url = '/api/CheckUEBRunStatus'
    connection = httplib.HTTPConnection(service_host_address)
    model_pkg_resources_with_run_status_processing = _get_ueb_model_pkg_resources_by_processing_status('Processing')
    if len(model_pkg_resources_with_run_status_processing) == 0:
        log.info(source + "No UEB model package has a run status of 'Processing' at this time")
        
    for resource in model_pkg_resources_with_run_status_processing:
        pkg_process_job_id = resource['RunJobID']
        resource_id = resource['id']
        service_request_url = service_request_api_url + '?uebRunJobID=' + pkg_process_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()
        
        if service_call_results.status == httplib.OK:
            request_processing_status = service_call_results.read()
            log.info(source + 'UEB model package run status as returned from App '
                              'server for RunJobID:%s is %s' % (pkg_process_job_id, request_processing_status))
        else:
            request_processing_status = "Error"
            log.error(source + 'HTTP status %d returned from App server when checking '
                               'run status for RunJobID:%s' % (service_call_results.status, pkg_process_job_id))
        
        connection.close()
        
        # update the resource processing status
        _update_ueb_model_pkg_run_status(resource_id, request_processing_status)        
        
@celery.task
def retrieve_ueb_packages():
    source = 'uebpackage.tasks.retrieve_ueb_packages():'
    global service_host_address
    service_request_api_url = '/api/GetUEBPackage'
    connection = httplib.HTTPConnection(service_host_address)
    request_resources_with_status_complete = _get_ueb_pkg_request_resources_by_processing_status('Complete')
    
    if len(request_resources_with_status_complete) == 0:
        log.info(source + "No UEB model package build request has a status of 'Complete' at this time")
        
    for resource in request_resources_with_status_complete:
        pkg_process_job_id = resource['PackageProcessJobID']
        resource_id = resource['id']
        service_request_url = service_request_api_url + '?packageID=' + pkg_process_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()
        
        if service_call_results.status == httplib.OK:
            log.info(source + 'UEB model package was received from App server for PackageJobID:%s' % pkg_process_job_id)
            try:
                _save_ueb_package_as_resource(service_call_results, resource_id)
            except Exception as e:
                log.error(source + 'Failed to save ueb model package as a resource '
                                   'for PackageJobID:%s\nException:%s' % (pkg_process_job_id, e))
                break

            # update the resource processing status
            request_processing_status = 'Package available'
              
            log.info(source + 'UEB model package build request status was '
                              'updated to Package available for request resource ID:%s' % resource_id)
        else:
            log.error(source + 'HTTP status %d returned from App server when retrieving '
                               'UEB model package for PackageJobID:'
                               '%s' % (service_call_results.status, pkg_process_job_id))
            request_processing_status = 'Error'
        
        connection.close()
        
        _update_ueb_request_process_status(resource_id, request_processing_status) 
        
    return


def retrieve_ueb_run_output_packages():
    source = 'uebpackage.tasks.retrieve_ueb_run_output_packages():'
    global service_host_address
    service_request_api_url = '/api/UEBModelRunOutput'
    connection =  httplib.HTTPConnection(service_host_address)
    model_pkg_resources_with_run_status_complete = _get_ueb_model_pkg_resources_by_processing_status('Complete')
    
    if len(model_pkg_resources_with_run_status_complete) == 0:
        log.info(source + "No UEB model package has a run status of 'Complete' at this time.")
        
    for resource in model_pkg_resources_with_run_status_complete:
        pkg_process_job_id = resource['RunJobID']
        resource_id = resource['id']
        service_request_url = service_request_api_url + '?uebRunJobID=' + pkg_process_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()
        
        if service_call_results.status == httplib.OK:            
            _save_ueb_output_package_as_resource(service_call_results, resource_id)   
            log.info(source + 'UEB model output package was received from App '
                              'server for RunJobID:%s' % pkg_process_job_id)
            # update the resource processing status
            request_processing_status = 'Output package available'
            
            log.info(source + 'UEB model package run status was updated to Output '
                              'package available for model package resource ID:%s' % resource_id)
        else:
            log.error(source + 'HTTP status %d returned from App server when '
                               'retrieving UEB model output package for '
                               'RunJobID:%s' % (service_call_results.status, pkg_process_job_id))
            request_processing_status = 'Error'
        
        _update_ueb_model_pkg_run_status(resource_id, request_processing_status)   
        connection.close()
        
    return


def _save_ueb_package_as_resource(service_call_results, pkg_request_resource_id):
    source = 'uebpackage.tasks._save_ueb_package_as_resource():'
    # get the matching resource object
    resource_obj = base.model.Resource.get(pkg_request_resource_id)
    related_pkg_obj = resource_obj.resource_group.package
           
    pkg_id = related_pkg_obj.id
    
    ckan_default_dir = '/tmp/ckan'
    # create a directory for saving the file
    # this will be a dir in the form of: /tmp/ckan/{random_id}
    random_id = base.model.types.make_uuid()
    destination_dir = os.path.join(ckan_default_dir, random_id)    
    os.makedirs(destination_dir)
    
    file = os.path.join(destination_dir, 'ueb_model_pkg.zip')
    
    bytes_to_read = 16 * 1024
    
    try:
        with open(file, 'wb') as file_obj:
            while True:
                data = service_call_results.read(bytes_to_read)
                if not data:
                    break
                file_obj.write(data)
    except Exception as e:       
        log.error(source + 'Failed to save the ueb_package zip file to temporary '
                           'location for package request resource ID: %s \n '
                           'Exception: %s' % (pkg_request_resource_id, e))
        raise e

    log.info(source + 'ueb_package zip file was saved to temporary location for '
                      'package request resource ID: %s' % pkg_request_resource_id)
        
    # upload the file to CKAN file store
    resource_metadata = _upload_file(file)
    if resource_metadata:
        log.info(source + 'UEB model package was uploaded for request resource ID:%s' % pkg_request_resource_id)  
    else:
        log.error(source + 'Failed to upload ueb_package zip file as a resource '
                           'for package request resource ID: %s' % pkg_request_resource_id)
        return
    
    # retrieve some of the file meta data
    resource_url = resource_metadata.get('_label') # this will return datetime stamp/filename
    
    resource_url = '/storage/f/' + resource_url  
    if resource_url.startswith('/'):
        resource_url = base.config.get('ckan.site_url','').rstrip('/') + resource_url
    else:
        resource_url = base.config.get('ckan.site_url','') + resource_url
        
    resource_created_date = resource_metadata.get('_creation_date')
    resource_name = resource_metadata.get('filename_original')
    resource_size = resource_metadata.get('_content_length')
    
    # add the uploaded ueb model pkg data file as a resource to the dataset
    resource_create_action = tk.get_action('resource_create') 
    context = {'model': base.model, 'session': base.model.Session, 'save': 'save' }
    user = uebhelper.get_site_user()
    context['user'] = user.get('name')
    context['ignore_auth'] = True
    context['validate'] = False
    
    #A value for key 'message" in the context must be set to 
    # avoid a bug in line#192 of the update.py under lib/action
    # without this, a TypeError will occur (TypeError:No object(name:translator) has been registered for this thread)
    context['message'] = 'Auto uploaded model package '
    
    data_dict = {
                "package_id": pkg_id, # id of the package/dataset to which the resource needs to be added
                "url": resource_url,
                "name": resource_name,
                "created": resource_created_date,
                "format": 'zip',
                "size": resource_size,
                "description": 'UEB Model Package_' + str(datetime.now()),
                "ResourceType": 'UEB Input Package'      # extra metadata
                }
    
    is_resource_add_success = False
    try:        
        resource_create_action(context, data_dict)
        is_resource_add_success = True
        log.info(source + 'UEB model package was added as a resource for '
                          'request resource ID:%s' % pkg_request_resource_id)
    except Exception as e:
        log.error(source + 'Failed to add UEB model package as a resource for '
                           'request resource ID:%s \nException: %s' % (pkg_request_resource_id, e))
        pass
    
    if is_resource_add_success:
        # update the related dataset
        data_dict = {'extras': {'IsInputPackageAvailable': 'Yes'}}
        update_msg = 'system auto updated ueb package dataset'
        background_task = True
        try:
            updated_package = uebhelper.update_package(pkg_id, data_dict, update_msg, background_task)
            log.info(source + 'UEB model package dataset was updated as a result of '
                              'receiving model input package for dataset:%s' % updated_package['name'])
        except Exception as e:
            log.error(source + 'Failed to update UEB model package dataset after '
                               'receiving model input package for request resource ID:%s \n'
                               'Exception: %s' % (pkg_request_resource_id, e))
            pass
    return


def _save_ueb_output_package_as_resource(service_call_results, model_input_pkg_resource_id):
    source = 'uebpackage.tasks._save_ueb_output_package_as_resource():'
    # get the matching resource object
    resource_obj = base.model.Resource.get(model_input_pkg_resource_id)
    related_pkg_obj = resource_obj.resource_group.package
           
    pkg_id = related_pkg_obj.id
    
    ckan_default_dir = '/tmp/ckan'
    # create a directory for savig the file
    # this will be a dir in the form of: /tmp/ckan/{random_id}
    random_id = base.model.types.make_uuid()
    destination_dir = os.path.join(ckan_default_dir, random_id)    
    os.makedirs(destination_dir)
    
    ueb_output_pkg_file = os.path.join(destination_dir, 'ueb_model_output_pkg.zip')
    
    bytes_to_read = 16 * 1024
    
    try:
        with open(ueb_output_pkg_file, 'wb') as file_obj:
            while True:
                data = service_call_results.read(bytes_to_read)
                if not data:
                    break
                file_obj.write(data)
    except Exception as e:       
        log.error(source + 'Failed to save the ueb model output package zip file to '
                           'temporary location for package request resource ID: %s \n '
                           'Exception: %s' % (model_input_pkg_resource_id, e))
        pass
        return
    
    log.info(source + 'ueb model output package zip file was saved to temporary location '
                      'for package request resource ID: %s' % model_input_pkg_resource_id)
        
    # upload the file to CKAN file store
    resource_metadata = _upload_file(ueb_output_pkg_file)
    if resource_metadata:
        log.info(source + 'UEB model output package was uploaded for model input '
                          'package resource ID:%s' % model_input_pkg_resource_id)
    else:
        log.error(source + 'Failed to upload ueb model output package zip file '
                           'as a resource for model input package resource ID: %s' % model_input_pkg_resource_id)
        return
    
    # retrieve some of the file meta data
    resource_url = resource_metadata.get('_label')  # this will return datetime stamp/filename
    resource_url = '/storage/f/' + resource_url  
    if resource_url.startswith('/'):
        resource_url = base.config.get('ckan.site_url','').rstrip('/') + resource_url
    else:
        resource_url = base.config.get('ckan.site_url','') + resource_url
        
    resource_created_date = resource_metadata.get('_creation_date')
    resource_name = resource_metadata.get('filename_original')
    resource_size = resource_metadata.get('_content_length')
    
    # add the uploaded ueb model pkg data file as a resource to the dataset
    resource_create_action = tk.get_action('resource_create') 
    context = {'model': base.model, 'session': base.model.Session, 'save': 'save' }
    user = uebhelper.get_site_user()
    context['user'] = user.get('name')
    context['ignore_auth'] = True
    context['validate'] = False
    
    #A value for key 'message" in the context must be set to 
    # avoid a bug in line#192 of the update.py under lib/action
    # without this, a TypeError will occur (TypeError:No object(name:translator) has been registered for this thread)
    context['message'] =  'Auto uploaded model output package ' 
    
    data_dict = {
                "package_id": pkg_id,  # id of the package/dataset to which the resource needs to be added
                "url": resource_url,
                "name": resource_name,
                "created": resource_created_date,
                "format":"zip",
                "size": resource_size,
                "description": 'UEB Model Output Package_' + str(datetime.now()),
                "ResourceType": 'UEB Output Package'      # extra metadata
                }
    
    is_resource_add_success = False
    try:        
        resource_create_action(context, data_dict)
        is_resource_add_success = True
        log.info(source + 'UEB model output package was added as a resource for '
                          'model input package resource ID:%s' % model_input_pkg_resource_id)
    except Exception as e:
        log.error(source + 'Failed to add UEB model output package as a resource '
                           'for model input package resource ID:%s \n Exception: %s' % (model_input_pkg_resource_id, e))
        pass
    
    if is_resource_add_success:
        # update the related dataset
        data_dict = {'extras': {'IsOutputPackageAvailable': 'Yes'}}
        update_msg = 'system auto updated ueb package dataset'
        background_task = True
        try:
            updated_package = uebhelper.update_package(pkg_id, data_dict, update_msg, background_task)
            log.info(source + 'UEB model package dataset was updated as a result of '
                              'receiving model output package for dataset:%s' % updated_package['name'])
        except Exception as e:
            log.error(source + 'Failed to update UEB model package dataset after receiving '
                               'model output package for model input package resource ID:%s \n '
                               'Exception: %s' % (model_input_pkg_resource_id, e))
            pass
    return


def _upload_file(file_path):
    """
    uploads a file to ckan filestore as and returns file metadata
    related to its existance in ckan
    param file_path: name of the file with its current location (path)
    """
    source = 'uebpackage.tasks._upload_file():'
    # this code has been implemented based on the code for the upload_handle() method
    # in storage.py    
    bucket_id = base.config.get('ckan.storage.bucket', 'default')    
    ts = datetime.now().isoformat().split(".")[0]  # '2010-07-08T19:56:47'    
    file_name  = os.path.basename(file_path).replace(' ', '-') # ueb request.txt -> ueb-request.txt
    file_key = os.path.join(ts, file_name) 
    label = file_key
    params = {'filename_original': os.path.basename(file_path), 'key': file_key}

    try:
        with open(file_path, 'r') as file_obj:        
            ofs = storage.get_ofs()
            resource_metadata = ofs.put_stream(bucket_id, label, file_obj, params)
    except Exception as e:
        log.error(source + 'Failed to upload file: %s \nException %s' % (file_path, e))
        resource_metadata = None
        pass
    
    if resource_metadata:
        log.info(source + 'File upload was successful for file: %s' % file_path)
                 
    return resource_metadata 
   

def _update_ueb_request_process_status(resource_id, status):
    data_dict = {'PackageProcessingStatus': status}
    update_msg = 'system auto updated ueb package request status'
    background_task = True
    uebhelper.update_resource(resource_id, data_dict, update_msg, background_task)


def _update_ueb_model_pkg_run_status(resource_id, status):
    data_dict = {'UEBRunStatus': status}
    update_msg = 'system auto updated ueb model package run status'
    background_task = True
    uebhelper.update_resource(resource_id, data_dict, update_msg, background_task)


def _get_ueb_pkg_request_resources_by_processing_status(status):    
    """
    Returns a list of package request resources that are currently
    have status set to value provided by the param 'status'
    """
    
    # note: the list of resources returned by the following action may contain
    # any deleted resources
    resource_search_action = tk.get_action('resource_search')
    
    context = {}
    # get the resource that has the format field set to zip and description field contains 'shape'
    #data_dict = {'query': ['PackageProcessingStatus:Processing']}
    data_dict = {'query': ['PackageProcessingStatus:' + status]}
    matching_resources = resource_search_action(context, data_dict)['results']
    
    ueb_pkg_active_requests = []
    for file_resource in matching_resources:        
        # filterout any deleted resources        
        active_resource = uebhelper.get_resource(file_resource['id'])
        if not active_resource:
            continue   
        ueb_pkg_active_requests.append(active_resource)
        
    return ueb_pkg_active_requests


def _get_ueb_model_pkg_resources_by_processing_status(status):    
    """
    Returns a list of model package resources that are currently
    have status set to value provided by the param 'status'
    """
    
    # note: the list of resources returned by the following action may contain
    # any deleted resources
    resource_search_action = tk.get_action('resource_search')
    
    context = {}
    # get the resource that has the UEBRunStatus field set to value of status variable
    data_dict = {'query': ['UEBRunStatus:' + status]}
    matching_resources = resource_search_action(context, data_dict)['results']
    
    ueb_pkg_active_requests = []
    for file_resource in matching_resources:        
        # filterout any deleted resources        
        active_resource = uebhelper.get_resource(file_resource['id'])
        if not active_resource:
            continue   
        ueb_pkg_active_requests.append(active_resource)
        
    return ueb_pkg_active_requests
