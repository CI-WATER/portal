import ckan.lib.base as base
import logging
import ckan.plugins as p
from ckan.lib.helpers import json
import ckan.lib.uploader as uploader
import ckan.lib.munge as munge
from datetime import datetime
import os
import shutil
import httplib
from .. import helpers as uebhelper


tk = p.toolkit
_ = tk._    # translator function

log = logging.getLogger('ckan.logic')


class PackagecreateController(base.BaseController):
        
    def packagecreateform(self):        

        tk.c.form_stage = 'stage_1'
        _set_context_to_shape_file_resources()

        # set default values for stage_1
        errors = {}
        data = {}
        data['domainfiletypeoption'] = 'polygon'
        data['domainshapefile'] = None
        data['startdate'] = '01/01/2011'
        data['enddate'] = '12/31/2011'
        data['buffersize'] = 500
        data['gridcellsize'] = 100
        error_summary = {}
        stages = ['active', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive',
                  'inactive', 'inactive']
        form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'stages': stages}
        return tk.render('packagecreateform.html', extra_vars=form_vars)
    
    #@validate(schema=TestFormSchema(), form='form', post_only=False, on_get=True)
    def submit(self):
        form_stage = tk.request.params['form_stage']
        if form_stage != 'stage_confirm':
            form_vars = _validate_form()
            if form_vars['error_summary']:
                if form_stage == 'stage_1':
                    _set_context_to_shape_file_resources()

                if form_stage in ['stage_2', 'stage_8', 'stage_9']:
                    tk.c.ueb_dat_files = _set_context_to_file_resources('dat')

                if form_stage in ['stage_3', 'stage_4', 'stage_5', 'stage_6', 'stage_8']:
                    tk.c.ueb_nc_files = _set_context_to_file_resources('nc')

                return tk.render('packagecreateform.html', extra_vars=form_vars)
        
        session = base.session
                
        if form_stage == 'stage_1':
            form_stage_number = 1
        elif form_stage == 'stage_2':
            form_stage_number = 2
        elif form_stage == 'stage_3':
            form_stage_number = 3
        elif form_stage == 'stage_4':
            form_stage_number = 4
        elif form_stage == 'stage_5':
            form_stage_number = 5
        elif form_stage == 'stage_6':
            form_stage_number = 6
        elif form_stage == 'stage_7':
            form_stage_number = 7
        elif form_stage == 'stage_8':
            form_stage_number = 8
        else:
            form_stage_number = 9
            
        if "submit" in tk.request.params:
            request_data_in_json = _get_package_request_in_json_format()  
            data = {}
            tk.c.selected_data = request_data_in_json
            tk.c.form_stage = 'stage_confirm' 
            form_vars['data'] = data
            form_vars['stages'] = {}
            return tk.render('packagecreateform.html', extra_vars=form_vars)
        elif 'confirm' in tk.request.params:
            return _process_ueb_pkg_request_submit()
            #   return 'Your UEB model package request is now in a queue for processing.'
        elif 'next' in tk.request.params:            
            form_stage_number += 1                     
        elif "prev" in tk.request.params:            
            form_stage_number -= 1
        else:   # 'edit' in tk.request.params:
            edit_stages = range(1, 10)
            for stage in edit_stages:
                edit_btn_name = 'edit_%d' % stage
                if edit_btn_name in tk.request.params:
                    form_stage_number = stage
                    break
             
            errors = {}
            data = {}
            error_summary = {}
            stages = []
            form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'stages': stages}

        form_stage = "stage_" + str(form_stage_number)
        if form_stage in session:
            data = session[form_stage] 
        else:
            data = _get_default_data(form_stage)            
            
        tk.c.form_stage = form_stage 
        if form_stage_number == 1:
            _set_context_to_shape_file_resources()
            stages = ['active', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive',
                      'inactive']
        elif form_stage_number == 2:
            tk.c.ueb_dat_files = _set_context_to_file_resources('dat')
            stages = ['inactive', 'active', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive',
                      'inactive']
        elif form_stage_number == 3:
            tk.c.ueb_nc_files = _set_context_to_file_resources('nc')
            stages = ['inactive', 'inactive', 'active', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive',
                      'inactive']
        elif form_stage_number == 4:
            tk.c.ueb_nc_files = _set_context_to_file_resources('nc')
            stages = ['inactive', 'inactive', 'inactive', 'active', 'inactive', 'inactive', 'inactive', 'inactive',
                      'inactive']
        elif form_stage_number == 5:
            tk.c.ueb_nc_files = _set_context_to_file_resources('nc')
            stages = ['inactive', 'inactive', 'inactive', 'inactive', 'active', 'inactive', 'inactive', 'inactive',
                      'inactive']
        elif form_stage_number == 6:
            tk.c.ueb_nc_files = _set_context_to_file_resources('nc')
            stages = ['inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'active', 'inactive', 'inactive',
                      'inactive']
        elif form_stage_number == 7:
            stages = ['inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'active', 'inactive',
                      'inactive']
        elif form_stage_number == 8:
            tk.c.ueb_dat_files = _set_context_to_file_resources('dat')
            tk.c.ueb_nc_files = _set_context_to_file_resources('nc')
            stages = ['inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'active',
                      'inactive']
        else:
            tk.c.ueb_dat_files = _set_context_to_file_resources('dat')
            stages = ['inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive',
                      'active']
            
        form_vars['data'] = data
        form_vars['stages'] = stages
        return tk.render('packagecreateform.html', extra_vars=form_vars)

    def check_package_build_status(self, pkg_id):

        """
        Retrievs the status of the model package build process from the app server for a given model configuration
        dataset
        @param pkg_id: id of the model configuration dataset for which the package build status to be obtained
        @return: ajax_response object
        """
        source = 'uebpackage.packagecreate.check_package_build_status():'
        service_host_address = uebhelper.StringSettings.app_server_host_address
        service_request_api_url = uebhelper.StringSettings.app_server_api_check_ueb_package_build_status
        connection = httplib.HTTPConnection(service_host_address)
        package = uebhelper.get_package(pkg_id)
        ajax_response = uebhelper.AJAXResponse()
        ajax_response.success = False
        ajax_response.message = "Not a valid package for status check"
        if package['type'] == 'model-configuration':
            if package.get('processing_status', None):
                if package['processing_status'] == 'In Queue' or package['processing_status'] == 'Processing':
                    pkg_process_job_id = package.get('package_build_request_job_id', None)
                    pkg_current_processing_status = package.get('processing_status', None)
                    if pkg_process_job_id:
                        service_request_url = service_request_api_url + '?packageID=' + pkg_process_job_id
                        connection.request('GET', service_request_url)
                        service_call_results = connection.getresponse()
                        if service_call_results.status == httplib.OK:
                            request_processing_status = service_call_results.read()
                            log.info(source + 'UEB model package build status as returned from App server '
                                              'for PackageJobID:%s is %s' % (pkg_process_job_id,
                                                                             request_processing_status))
                        else:
                            request_processing_status = uebhelper.StringSettings.app_server_job_status_error
                            log.error(source + 'HTTP status %d returned from App server when checking '
                                   'status for PackageJobID:%s' % (service_call_results.status, pkg_process_job_id))
                            ajax_response.success = False
                            ajax_response.message = "Error in checking status"

                        connection.close()

                        # update the dataset if the status has changed
                        if pkg_current_processing_status != request_processing_status:
                            if request_processing_status == 'Success':
                                data_dict = {'processing_status': request_processing_status,
                                             'package_availability': uebhelper.StringSettings.app_server_job_status_package_ready_to_retrieve}
                            else:
                                data_dict = {'processing_status': request_processing_status}

                            uebhelper.update_package(pkg_id, data_dict, backgroundTask=False)

                        ajax_response.success = True
                        ajax_response.message = "Status check was successful"
                        ajax_response.json_data = request_processing_status

        return ajax_response.to_json()

    def retrieve_input_package(self, pkg_id):

        """
        Retrieves the model input package from the app server and saves it as a new dataset
        @param pkg_id: id of the model configuration dataset for which the model input package to be retrieved
        @rtype: ajax_response object
        """

        source = 'uebpackage.packagecreate.retrieve_input_package():'
        service_host_address = uebhelper.StringSettings.app_server_host_address
        service_request_api_url = uebhelper.StringSettings.app_server_api_get_ueb_package_url
        connection = httplib.HTTPConnection(service_host_address)
        package = uebhelper.get_package(pkg_id)
        ajax_response = uebhelper.AJAXResponse()
        ajax_response.success = False
        ajax_response.message = "Not a valid UEB model configuration datatset for model package retrieval"
        if package['type'] == 'model-configuration':
            if package.get('processing_status', None):
                if package['package_availability'] == 'Ready to retrieve':
                    pkg_process_job_id = package.get('package_build_request_job_id', None)
                    pkg_current_availability_status = package.get('package_availability', None)
                    if pkg_process_job_id:
                        service_request_url = service_request_api_url + '?packageID=' + pkg_process_job_id
                        connection.request('GET', service_request_url)
                        service_call_results = connection.getresponse()
                        if service_call_results.status == httplib.OK:
                            log.info(source + 'UEB model package was received from App server for PackageJobID:%s' % pkg_process_job_id)
                            try:
                                _save_ueb_package_as_dataset(service_call_results, pkg_id)
                                pkg_availability_status = uebhelper.StringSettings.app_server_job_status_package_available
                                ajax_response.success = True
                                ajax_response.message = "Model package retrieval was successful"
                                ajax_response.json_data = pkg_availability_status
                            except Exception as e:
                                log.error(source + 'Failed to save ueb model package as a new dataset '
                                                   'for model configuration dataset ID:%s\nException:%s' % (pkg_id, e))
                                pkg_availability_status = uebhelper.StringSettings.app_server_job_status_error
                                ajax_response.success = False
                                ajax_response.message = "Failed to save the retrieved model package"
                                ajax_response.json_data = pkg_availability_status
                        else:
                            log.error(source + 'HTTP status %d returned from App server when retrieving '
                                               'UEB model package for PackageJobID:'
                                               '%s' % (service_call_results.status, pkg_process_job_id))
                            pkg_availability_status = uebhelper.StringSettings.app_server_job_status_error
                            ajax_response.success = False
                            ajax_response.message = "Error in retrieving the model package"
                            ajax_response.json_data = pkg_availability_status

                        connection.close()

                        # update the related model-configuration dataset status
                        data_dict = {'package_availability': pkg_availability_status}
                        update_msg = 'updated package availability status'
                        background_task = False

                        if pkg_current_availability_status != pkg_availability_status:
                            try:
                                updated_package = uebhelper.update_package(pkg_id, data_dict, update_msg,
                                                                           background_task)
                                log.info(source + 'UEB model configuration dataset was updated as a result of '
                                                  'receiving model input package for dataset:%s'
                                         % updated_package['name'])

                            except Exception as e:
                                log.error(source + 'Failed to update UEB model configuration dataset after '
                                                   'receiving model input package for dataset ID:%s \n'
                                                   'Exception: %s' % (pkg_id, e))
                                pass

        return ajax_response.to_json()


def _save_ueb_package_as_dataset(service_call_results, model_config_dataset_id):

    """
    Saves the model input package obtained for the app server as a new dataset
    @param service_call_results: service response obtained from the app server
    @param model_config_dataset_id: id of the model configuration dataset for which the generated model package to be
    retrieved.
    @return:
    """
    source = 'uebpackage.packagecreate._save_ueb_package_as_dataset():'
    ckan_default_dir = uebhelper.StringSettings.ckan_user_session_temp_dir  # '/tmp/ckan'

    # get the matching model configuration dataset object
    model_config_dataset_obj = base.model.Package.get(model_config_dataset_id)
    model_config_dataset_title = model_config_dataset_obj.title
    model_config_dataset_owner_org = model_config_dataset_obj.owner_org
    model_config_dataset_author = model_config_dataset_obj.author

    # create a directory for saving the file
    # this will be a dir in the form of: /tmp/ckan/{random_id}
    random_id = base.model.types.make_uuid()
    destination_dir = os.path.join(ckan_default_dir, random_id)
    os.makedirs(destination_dir)

    model_pkg_filename = uebhelper.StringSettings.ueb_input_model_package_default_filename   # 'ueb_model_pkg.zip'
    model_pkg_file = os.path.join(destination_dir, model_pkg_filename)

    bytes_to_read = 16 * 1024

    try:
        with open(model_pkg_file, 'wb') as file_obj:
            while True:
                data = service_call_results.read(bytes_to_read)
                if not data:
                    break
                file_obj.write(data)
    except Exception as e:
        log.error(source + 'Failed to save the ueb_package zip file to temporary '
                           'location for UEB model configuration dataset ID: %s \n '
                           'Exception: %s' % (model_config_dataset_id, e))
        raise e

    log.info(source + 'ueb_package zip file was saved to temporary location for '
                      'UEB model configuration dataset ID: %s' % model_config_dataset_id)

    user = uebhelper.get_site_user()
    # create a package
    package_create_action = tk.get_action('package_create')

    # create unique package name using the current time stamp as a postfix to any package name
    unique_postfix = datetime.now().isoformat().replace(':', '-').replace('.', '-').lower()
    pkg_title = model_config_dataset_title

    data_dict = {
                    'name': 'model_package_' + unique_postfix,  # this needs to be unique as required by DB
                    'type': 'model-package',  # dataset type as defined in custom dataset plugin
                    'title': pkg_title,
                    'owner_org': model_config_dataset_owner_org,
                    'author': model_config_dataset_author,
                    'notes': 'UEB model package',
                    'pkg_model_name': 'UEB',
                    'model_version': '1.0',
                    'north_extent': '',
                    'south_extent': '',
                    'east_extent': '',
                    'west_extent': '',
                    'simulation_start_day': '',
                    'simulation_end_day': '',
                    'time_step': '',
                    'package_type': u'Input',
                    'package_run_status': 'Not yet submitted',
                    'package_run_job_id': '',
                    'dataset_type': 'model-package'
                 }

    context = {'model': base.model, 'session': base.model.Session, 'ignore_auth': True, 'user': user.get('name'), 'save': 'save'}
    try:
        pkg_dict = package_create_action(context, data_dict)
        log.info(source + 'A new dataset was created for UEB input model package with name: %s' % data_dict['title'])
    except Exception as e:
        log.error(source + 'Failed to create a new dataset for ueb input model package for'
                           ' the related model configuration dataset title: %s \n Exception: %s' % (pkg_title, e))
        raise e

    if not 'resources' in pkg_dict:
        pkg_dict['resources'] = []

    try:
        file_name = model_pkg_filename  # munge.munge_filename(model_pkg_filename)
        resource = {'url': file_name, 'url_type': 'upload'}
        upload = uploader.ResourceUpload(resource)
        upload.filename = file_name
        upload.upload_file = open(model_pkg_file, 'r')
        data_dict = {'format': 'zip', 'name': file_name, 'url': file_name, 'url_type': 'upload'}
        pkg_dict['resources'].append(data_dict)
    except Exception as e:
        log.error(source + ' Failed to save the model package zip file as'
                            ' a resource.\n Exception: %s' % e)

    try:
        context['defer_commit'] = True
        context['use_cache'] = False
        # update the package
        package_update_action = tk.get_action('package_update')
        package_update_action(context, pkg_dict)
        context.pop('defer_commit')
    except Exception as e:
        log.error(source + ' Failed to update the new dataset for adding the input model package zip file as'
                            ' a resource.\n Exception: %s' % e)

        raise e

    # Get out resource_id resource from model as it will not appear in
    # package_show until after commit
    upload.upload(context['package'].resources[-1].id, uploader.get_max_resource_size())
    base.model.repo.commit()

    # update the related model configuration dataset to show that the package is available
    data_dict = {'package_availability': 'Available'}
    update_msg = 'system auto updated ueb package dataset'
    background_task = False
    try:
        updated_package = uebhelper.update_package(model_config_dataset_id, data_dict, update_msg, background_task)
        log.info(source + 'UEB model configuration dataset was updated as a result of '
                          'receiving model input package for dataset:%s' % updated_package['name'])
    except Exception as e:
        log.error(source + 'Failed to update UEB model configuration dataset after '
                           'receiving model input package for dataset ID:%s \n'
                           'Exception: %s' % (model_config_dataset_id, e))
        raise e


def _process_ueb_pkg_request_submit():
    pkgname = base.session['stage_1']['pkgname']
    selected_user_org = base.session['stage_1']['owner_org']
    ueb_pkg_request = _get_package_request_in_json_format() 
    selected_file_ids = ueb_pkg_request['selected_file_ids']
    ueb_pkg_request_in_json = ueb_pkg_request['ueb_req_json']
    model_configuration_pkg_id = _save_ueb_request_as_dataset(pkgname, selected_file_ids, selected_user_org)

    if model_configuration_pkg_id:
        request_zip_file = _create_ueb_pkg_build_request_zip_file(ueb_pkg_request_in_json, selected_file_ids)
        pkg_process_id = _send_request_to_app_server(request_zip_file)
        job_status_queue = uebhelper.StringSettings.app_server_job_status_in_queue
        data_dict = {'package_build_request_job_id': pkg_process_id, 'processing_status': job_status_queue}
        uebhelper.update_package(model_configuration_pkg_id, data_dict)
        base.session.clear()
        tk.c.request_process_job_id = pkg_process_id
        return tk.render('package_build_request_submission.html')
    else:
        # TODO: show error page
        return "Error"


def _send_request_to_app_server(request_zip_file):
    source = 'uebpackage.uebpackage.packagerequest._send_request_to_app_server():'
    service_host_address = uebhelper.StringSettings.app_server_host_address
    service_request_url = uebhelper.StringSettings.app_server_api_generate_ueb_package_url
    connection = httplib.HTTPConnection(service_host_address)
    headers = {'Content-Type': 'application/text', 'Accept': 'application/text'}
    # get request data from the zip file
    with open(request_zip_file, 'r') as file_obj:
        file_data = file_obj.read()    
        request_body_content = file_data
    
    # call the service TODO: see if we can pass the open file object as request_body_content
    connection.request('POST', service_request_url, request_body_content, headers)
    
    # retrieve response
    service_call_results = connection.getresponse()
    package_id = None
    if service_call_results.status == httplib.OK:
        log.info(source + 'UEB model build package request was sent to app server')
        service_response_data = service_call_results.read()
        connection.close()
        # convert the json data from the app server to a python dict object
        service_response_dict = json.loads(service_response_data)
        package_id = service_response_dict.get('PackageID', None)
        response_msg = service_response_dict.get('Message', '')
        if not package_id:
            log.error(source + 'App server failed to process model package build request')
            tk.abort(400, _('App server failed to process model package build request: %s') % response_msg)        
    else:
        connection.close()
        tk.abort(400, _('App server failed to process model package build request: %s') % service_call_results.reason)
        
    # cleanup the temp data directory created previously
    #ckan_default_dir = _get_predefined_name('ckan_user_session_temp_dir') #'/tmp/ckan'
    ckan_default_dir = uebhelper.StringSettings.ckan_user_session_temp_dir
    try:
        shutil.rmtree(ckan_default_dir)
    except:
        pass
    
    return package_id


def _update_request_resource_process_job_id(ueb_model_pkg_request_resource_id, pkg_process_id):
    
    """
    Updates a ueb model package request resource's 'extras' field to include
    PackageProcessJobID: param pkg_process_id
    Note that the extra field in resource table holds a json string

    param ueb_model_pkg_request_resource_id: id of the resource to be updated
    param pkg_process_id: package id returned from app server responsible for generating the model package
    """
    #matching_resource = _get_resource(ueb_model_pkg_request_resource_id)    
    #resource_update_action = tk.get_action('resource_update')
    #context = {'model': base.model, 'session': base.model.Session,
    #           'user': base.c.user or base.c.author}
    
    # the data_dict needs to be the resource metadata for an existing resource
    # (all fields and their corresponding values)
    # once we have retrieved a resource we can update value for any fields
    # by assigning new value to that field except for the 'extras' field.
    # the extras field is not part of the resource metadata when you retrieve a resource
    # from filestore. Since the extras field holds a json string that contains key/value pairs,
    # the way to update the extra field is to add a new key/value pair
    # to the resource metadata dict object where the key is not the name of a field in resource table.
    # For example, as shown below, we are storing a value for PackageProcessJobID
    # which will be added/updated to the existing json string stored in the extras field

    data_dict = {'PackageProcessJobID': pkg_process_id}
    updated_resource = _update_resource(ueb_model_pkg_request_resource_id, data_dict)
    return updated_resource


def _update_request_resource_process_status(ueb_model_pkg_request_resource_id, status):
    data_dict = {'PackageProcessingStatus': status}
    updated_resource = _update_resource(ueb_model_pkg_request_resource_id, data_dict)
    return updated_resource


def _update_resource(resource_id, data_dict):
    """
    Updates a resource identified by resource_id
    with fields and corresponding values found in the data_dict
    Note: if key is not a field of the resource table in the data_dict
    that key/value pair will be added/updated to the 'extras' field of the resource
    """
    matching_resource = _get_resource(resource_id)    
    resource_update_action = tk.get_action('resource_update')
    context = {'model': base.model, 'session': base.model.Session,
               'user': tk.c.user or tk.c.author}
    
    for key, value in data_dict.items():
        matching_resource[key] = value
        
    updated_resource = resource_update_action(context, matching_resource)    
    return updated_resource


def _create_ueb_pkg_build_request_zip_file(ueb_pkg_request_in_json, selected_file_ids):
    """
    Creates a zip file containing all the files the user selected in configuring
    ueb model as well as the text file in the form of a json string that contains
    all the parameters and their values selected.

    param ueb_pkg_request_in_json: json string that contains user package build request details
    param: selected_file_ids a dict in which each value is a file id
    rtype: a string representing the location and name of the zip file
    """
    #ckan_default_dir = _get_predefined_name('ckan_user_session_temp_dir') #'/tmp/ckan'
    ckan_default_dir = uebhelper.StringSettings.ckan_user_session_temp_dir
    # save the ueb request json string to the default directory specified by ckan_default_dir
    destination_session_dir = os.path.join(ckan_default_dir, base.session.id)
    destination_files_dir = os.path.join(destination_session_dir, 'files')
    if not os.path.isdir(destination_files_dir):
        os.makedirs(destination_files_dir)
    
    #ueb_request_json_file_name = _get_predefined_name('ueb_request_json_file_name')
    ueb_request_json_file_name = uebhelper.StringSettings.ueb_request_json_file_name
    request_file_json = os.path.join(destination_files_dir, ueb_request_json_file_name)
    with open(request_file_json, 'w') as file_obj:
        file_obj.write(ueb_pkg_request_in_json)
        
    resource_show_action = tk.get_action('resource_show')
    context = {'model': base.model, 'session': base.model.Session,
               'user': tk.c.user or tk.c.author}

    # get the storage path
    ckan_storage_path = os.path.join(uploader.get_storage_path(), 'resources')

    # for each file id, get the file object and write to the temp destination dir
    for file_id in selected_file_ids.values():
        # Note:4/22/2014: The way we are finding the filepath for a resource
        # no more works in the new ckan 2.2 as the storage strategy has changed
        # Refer to the uploader.py module and see how it gets the file path
        # from the id of the resource. Use that technique to read each of the
        # files to be part of the zip file
        # new code
        resource_file_path = os.path.join(ckan_storage_path, file_id[0:3], file_id[3:6], file_id[6:])
        resource_file_obj = open(resource_file_path, 'r')
        resource_file_obj.seek(0)
        data_dict = {'id': file_id}
        matching_file_resource = resource_show_action(context, data_dict)
        file_name = matching_file_resource.get('name')
        # save file to the temp dir
        dest_file_path = os.path.join(destination_files_dir, file_name)
        dest_file_obj = open(dest_file_path, 'wb+')
        while True:
            data = resource_file_obj.read(2 ** 20)
            if not data:
                break
            dest_file_obj.write(data)

        resource_file_obj.close()
        dest_file_obj.close()
                
    # zip all the files in the destination_files_dir to a new zip folder under the destination_session_dir
    # make a folder to store the zip file
    destination_zip_dir = os.path.join(destination_session_dir, 'zip')    
    os.mkdir(destination_zip_dir)
    destination_zip_file_path = os.path.join(destination_zip_dir, 'ueb_pkg_request') # leave out the extension here
    source_files_dir = destination_files_dir
    shutil.make_archive(destination_zip_file_path, format='zip', root_dir=source_files_dir)    
    zipped_request_file = destination_zip_file_path + '.zip'
    
    return zipped_request_file


def _set_context_to_shape_file_resources():

    """
    create a list of shape files in the system that are owned
    by the current user. If the user has uploaded it then he/she owns it.
    @return: None
    """

    geographic_fs_datasets = uebhelper.get_packages_by_dataset_type('geographic-feature-set')

    # for each resource we need only the id (id be used as the selection value) and the name for display
    file_resources = []
    resource = {'id': 0, 'name': 'Select a shape file ..'}
    file_resources.append(resource)
    for gfs_dataset in geographic_fs_datasets:
        gfs_resources = gfs_dataset['resources']
        for resource in gfs_resources:
            if resource['format'].lower() == 'zip' and \
                    (resource['resource_type'] == 'file.upload' or resource['url_type'] == 'upload') and \
                            resource['state'] == 'active':
                # check if the file resource is owned by the current user
                user_owns_resource = uebhelper.is_user_owns_resource(resource['id'], tk.c.user)
                if user_owns_resource:
                    selected_resource = {'id': resource['id'], 'name': resource['name']}
                    file_resources.append(selected_resource)

    tk.c.ueb_domain_shape_files = file_resources    


def _set_context_to_file_resources(file_extension):
    """
    This will create a list of all files that has
    extension of file_extension and return the matching list of
    resources
    """
    # TODO: save the list of file resources for a given extension type
    # in the session object so that we do not run this function for
    # each page of the form

    # note: resource_search returns a list of matching resources
    # that can include any deleted resources
    resource_search_action = tk.get_action('resource_search')
    context = {'model': base.model, 'session': base.model.Session,
               'user': tk.c.user or tk.c.author, 'for_view': True}

    # get the resource that has the format field set to file_extension
    # and resource_type to file.upload
    data_dict = {'query': ['format:' + file_extension]}
    shape_file_resources = resource_search_action(context, data_dict)['results']

    # for each resource we need only the id (id be used as the selection value) and the name for display
    file_resources = []
    resource = {'id': 0, 'name': 'Select a file ..'}
    file_resources.append(resource)
    for file_resource in shape_file_resources:
        resource = {}
        # filter out any deleted resources
        active_resource = _get_resource(file_resource['id'])
        if not active_resource:
            continue
        # filter out any resources that has resource_type as file.link
        if file_resource['resource_type'] == 'file.link':
            continue

        # check if the file resource is owned by the current user
        user_owns_resource = uebhelper.is_user_owns_resource(file_resource['id'], tk.c.user)

        if user_owns_resource:
            resource['id'] = file_resource['id']
            resource['name'] = file_resource['name']
            file_resources.append(resource)

    return file_resources


def _get_file_name_from_file_id(file_id):    
    matching_file_resource = _get_resource(file_id)
    return matching_file_resource['name']


def _get_file_id_from_file_name(package_id, filename):    
    package_show_action = tk.get_action('package_show')
    context = {'model': base.model, 'session': base.model.Session,
               'user': tk.c.user or tk.c.author}
    
    # get the dataset/package that has the id equal to the given dataset/package name
    # (note: name is unique in package table)
    data_dict = {'id': package_id}
    matching_package_with_resources = package_show_action(context, data_dict)
    files = matching_package_with_resources['resources']
    for r_file in files:
        if r_file['name'] == filename:
            return r_file['id']
    
    return '' 


def _get_package(pkg_id_or_name):  
    package_show_action = tk.get_action('package_show')
    context = {'model': base.model, 'session': base.model.Session,
               'user': tk.c.user or tk.c.author}
    
    # get the resource that has the id equal to the given resource id or name
    data_dict = {'id': pkg_id_or_name }
    matching_package_with_resources = package_show_action(context, data_dict)  
    
    return matching_package_with_resources


def _get_resource(resource_id):
    resource_show_action = tk.get_action('resource_show')
    context = {'model': base.model, 'session': base.model.Session,
               'user': tk.c.user or tk.c.author}
    
    # get the resource that has the id equal to the given resource id
    data_dict = {'id': resource_id}
    matching_resource = None
    
    # if the resource does not exist or it is a deleted resource
    # resource_show action will throw ObjectNotFound exception
    try:
        matching_resource = resource_show_action(context, data_dict)
    except tk.ObjectNotFound:
        pass
    
    return matching_resource


def _get_ueb_pkg_request_resources_pending_processing():    
    """
    Returns a list of package request resources that are currently
    have status set to 'Processing'
    """
    resource_search_action = tk.get_action('resource_search')
    context = {'model': base.model, 'session': base.model.Session,
               'user': tk.c.user or tk.c.author}
    
    # get the resource that has the format field set to zip and description field contains 'shape'
    data_dict = {'query': ['PackageProcessingStatus:Processing']}
    matching_resources = resource_search_action(context, data_dict)['results']
    
    return matching_resources


def _validate_form():
    form_stage = tk.request.params['form_stage']
    
    if form_stage == 'stage_1':
        return _validate_stage_one()
    
    if form_stage == 'stage_2':
        return _validate_stage_two()
    
    if form_stage == 'stage_3':
        return _validate_stage_three()
    
    if form_stage == 'stage_4':
        return _validate_stage_four()
    
    if form_stage == 'stage_5':
        return _validate_stage_five()
    
    if form_stage == 'stage_6':
        return _validate_stage_six()
    
    if form_stage == 'stage_7':
        return _validate_stage_seven()
    
    if form_stage == 'stage_8':
        return _validate_stage_eight()
    
    if form_stage == 'stage_9':
        return _validate_stage_nine()


def _validate_stage_one():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary':error_summary, 'stages': stages}
    form_stage = 'stage_1'
    pkgname = tk.request.params['pkgname']  
    pkgdescription = tk.request.params['pkgdescription'] 
    domainfiletypeoption = tk.request.params['domainfiletypeoption']
    domainshapefile = tk.request.params['domainshapefile']
    domainnetcdfile = tk.request.params['domainnetcdfile']
    domainnetcdffileformat = tk.request.params['domainnetcdffileformat']
    buffersize = tk.request.params['buffersize']
    gridcellsize = tk.request.params['gridcellsize']
    startdate = tk.request.params['startdate']
    enddate = tk.request.params['enddate']
    timestep = tk.request.params['timestep']
    owner_org = tk.request.params['owner_org']

    data['pkgname'] = pkgname
    data['pkgdescription'] = pkgdescription
    data['domainfiletypeoption'] = domainfiletypeoption    
    data['domainshapefile'] = domainshapefile
    data['domainnetcdfile'] = domainnetcdfile
    data['domainnetcdffileformat'] = domainnetcdffileformat
    data['buffersize'] = buffersize
    data['gridcellsize'] = gridcellsize
    data['startdate'] = startdate
    data['enddate'] = enddate
    data['timestep'] = timestep
    data['owner_org'] = owner_org
    
    for key in data:
        errors[key] = []
        
    context = {}   
    if form_stage not in session:
        session[form_stage] = {}
         
    session[form_stage] = data    
    session.save()
    
    not_empty_check = tk.get_validator('not_empty')   # not_empty(key, data, errors, context):
                
    # Put all the validation functions in a list
    # so that we can execute them all even if any one of them throws validation error    
    actions = [
                lambda: not_empty_check('pkgname', data, errors, context),
                lambda: not_empty_check('buffersize', data, errors, context),
                lambda: not_empty_check('gridcellsize', data, errors, context),
                lambda: not_empty_check('startdate', data, errors, context),
                lambda: not_empty_check('enddate', data, errors, context),
              ]

    if data['owner_org'] == '':
        data['owner_org'] = None
        try:
            not_empty_check('owner_org', data, errors, context)
        except:
           pass

    if domainfiletypeoption == 'polygon':
        if data['domainshapefile'] == '0':
            data['domainshapefile'] = None

        actions.append(lambda: not_empty_check('domainshapefile', data, errors, context))
    else:
        errors['domainnetcdfile'].append('Use of netCDF file for domain not yet implemented.')

        # TODO: the following 3 lines need to be uncommented when domain netcdf file use is implemented
        # at the app server
        '''
        actions.append(lambda: not_empty_check('domainnetcdfile', data, errors, context))
        actions.append(lambda: not_empty_check('domainnetcdffileformat', data, errors, context))

        # check if the file selected as domain netcdf file has already been selected for any other input
        _validate_file_selection(data, errors, 'domainnetcdffile', 'domain netCDF')
        '''

    for action in actions:
        try:
            action()
        except:
            pass

    # Check for numeric data type
    try:
        int(buffersize)
    except ValueError:
        errors['buffersize'].append('Buffer size should be an integer value')
    try:
        int(gridcellsize)
    except ValueError:
        errors['gridcellsize'].append('Grid cell size should be an integer value')
    
    if len(errors['startdate']) == 0:
        try:        
            date = datetime.strptime(startdate, '%m/%d/%Y')
            if date.year != 2011:
                errors['startdate'].append('Year should be 2011')
        except (TypeError, ValueError):
            errors['startdate'].append('Enter a date value')
    
    if len(errors['enddate']) == 0:
        try:
            date = datetime.strptime(enddate, '%m/%d/%Y')
            if date.year != 2011:
                errors['enddate'].append('Year should be 2011')
        except (TypeError, ValueError):
            errors['enddate'].append('Enter a date value')
    
    # Populate the error_summary list
    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value:  # error message exists
            error_summary[key] = value
        
    tk.c.form_stage = form_stage     
    stages = ['active', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_stage_two():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'stages': stages}
    form_stage = 'stage_2' 
    parametersfileoption = tk.request.params['parametersfileoption']  
    parametersfile = tk.request.params['parametersfile']  
    data['parametersfileoption'] = parametersfileoption
    data['parametersfile'] = parametersfile   
    errors['parametersfile'] = []
    context = {}   
    if form_stage not in session:
        session[form_stage] = {}
         
    session[form_stage] = data    
    session.save()
    
    not_empty_check = tk.get_validator('not_empty')   # not_empty(key, data, errors, context):
           
    if parametersfileoption == 'No':
        if data['parametersfile'] == '0':
            data['parametersfile'] = None
        try:
            not_empty_check('parametersfile', data, errors, context)
        except:
           pass

        # check if the file selected as parameters file has already been selected for any other input
        _validate_file_selection(data, errors, 'parametersfile', 'parameters')
    else:
        data['parametersfile'] = None

    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value:  # error message exists
            error_summary[key] = value
    
    tk.c.form_stage = form_stage 
    stages = ['inactive', 'active', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_stage_three():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'stages': stages}
    form_stage = 'stage_3' 
    usicoption = tk.request.params['usicoption']  
    usic = tk.request.params['usic']  
    usicgridfile = tk.request.params['usicgridfile']
    usicgridfileformat = tk.request.params['usicgridfileformat']
    
    wsisoption = tk.request.params['wsisoption']
    wsis = tk.request.params['wsis']
    wsisgridfile = tk.request.params['wsisgridfile']
    wsisgridfileformat = tk.request.params['wsisgridfileformat']
    
    ticoption = tk.request.params['ticoption']  
    tic = tk.request.params['tic']  
    ticgridfile = tk.request.params['ticgridfile']
    ticgridfileformat = tk.request.params['ticgridfileformat']
    
    wcicoption = tk.request.params['wcicoption']  
    wcic = tk.request.params['wcic']  
    wcicgridfile = tk.request.params['wcicgridfile']
    wcicgridfileformat = tk.request.params['wcicgridfileformat']
    
    data['usicoption'] = usicoption
    data['usic'] = usic  
    data['usicgridfile'] = usicgridfile
    data['usicgridfileformat'] = usicgridfileformat
    
    data['wsisoption'] = wsisoption
    data['wsis'] = wsis
    data['wsisgridfile'] = wsisgridfile
    data['wsisgridfileformat'] = wsisgridfileformat
    
    data['ticoption'] = ticoption
    data['tic'] = tic
    data['ticgridfile'] = ticgridfile
    data['ticgridfileformat'] = ticgridfileformat
    
    data['wcicoption'] = wcicoption
    data['wcic'] = wcic
    data['wcicgridfile'] = wcicgridfile
    data['wcicgridfileformat'] = wcicgridfileformat
    
    for key in data:
        errors[key] = []
     
    context = {}   

    not_empty_check = tk.get_validator('not_empty') 
    actions = []
    if usicoption == 'Constant':
        actions.append(lambda: not_empty_check('usic', data, errors, context))
        data['usicgridfile'] = None
    else:
        if data['usicgridfile'] == '0':  # value is 0 for option "Select a file ..'
            data['usicgridfile'] = None

        actions.append(lambda: not_empty_check('usicgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('usicgridfileformat', data, errors, context))

        # check if the file selected as energy content file has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'usicgridfile', 'energy content'))

    if wsisoption == 'Constant':
        actions.append(lambda: not_empty_check('wsis', data, errors, context))
        data['wsisgridfile'] = None
    else:
        if data['wsisgridfile'] == '0':
            data['wsisgridfile'] = None

        actions.append(lambda: not_empty_check('wsisgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('wsisgridfileformat', data, errors, context))

        # check if the file selected as water equivalent file has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'wsisgridfile', 'water equivalent'))

    if ticoption == 'Constant':
        actions.append(lambda: not_empty_check('tic', data, errors, context))
        data['ticgridfile'] = None
    else:
        if data['ticgridfile'] == '0':
            data['ticgridfile'] = None

        actions.append(lambda: not_empty_check('ticgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('ticgridfileformat', data, errors, context))

        # check if the file selected as snow surface dimensionless age file has already been selected
        # for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'ticgridfile', 'snow surface dimensionless age'))

    if wcicoption == 'Constant':
        actions.append(lambda: not_empty_check('wcic', data, errors, context))
        data['wcicgridfile'] = None
    else:
        if data['wcicgridfile'] == '0':
            data['wcicgridfile'] = None

        actions.append(lambda: not_empty_check('wcicgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('wcicgridfileformat', data, errors, context))

        # check if the file selected as canopy snow water equivalent file has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'wcicgridfile', 'snow water equivalent'))

    if form_stage not in session:
        session[form_stage] = {}

    session[form_stage] = data
    session.save()

    for action in actions:
        try:
            action()
        except:
            pass
        
    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value: # error message exists
            error_summary[key] = value
    
    tk.c.form_stage = form_stage 
    stages = ['inactive', 'inactive', 'active', 'inactive', 'inactive', 'inactive', 'inactive',
              'inactive', 'inactive']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_stage_four():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary':error_summary, 'stages':stages}
    form_stage = 'stage_4' 
    
    dfoption = tk.request.params['dfoption']  
    df = tk.request.params['df']  
    dfgridfile = tk.request.params['dfgridfile']
    dfgridfileformat = tk.request.params['dfgridfileformat']
    
    aepoption = tk.request.params['aepoption']  
    aep = tk.request.params['aep']  
    aepgridfile = tk.request.params['aepgridfile']
    aepgridfileformat = tk.request.params['aepgridfileformat']
    
    sbaroption = tk.request.params['sbaroption']  
    sbar = tk.request.params['sbar']  
    sbargridfile = tk.request.params['sbargridfile']
    sbargridfileformat = tk.request.params['sbargridfileformat']
    
    subalboption = tk.request.params['subalboption']  
    subalb = tk.request.params['subalb']  
    subalbgridfile = tk.request.params['subalbgridfile']
    subalbgridfileformat = tk.request.params['subalbgridfileformat']
    
    subtypeoption = tk.request.params['subtypeoption']  
    subtype = tk.request.params['subtype']  
    subtypegridfile = tk.request.params['subtypegridfile']
    subtypegridfileformat = tk.request.params['subtypegridfileformat']
    
    gsurfoption = tk.request.params['gsurfoption']  
    gsurf = tk.request.params['gsurf']  
    gsurfgridfile = tk.request.params['gsurfgridfile']
    gsurfgridfileformat = tk.request.params['gsurfgridfileformat']
    
    tslastoption = tk.request.params['ts_lastoption']  
    tslast = tk.request.params['ts_last']  
    tslastgridfile = tk.request.params['ts_lastgridfile']
    tslastgridfileformat = tk.request.params['ts_lastgridfileformat']
    
    data['dfoption'] = dfoption
    data['df'] = df  
    data['dfgridfile'] = dfgridfile
    data['dfgridfileformat'] = dfgridfileformat
    
    data['aepoption'] = aepoption
    data['aep'] = aep  
    data['aepgridfile'] = aepgridfile
    data['aepgridfileformat'] = aepgridfileformat
    
    data['sbaroption'] = sbaroption
    data['sbar'] = sbar  
    data['sbargridfile'] = sbargridfile
    data['sbargridfileformat'] = sbargridfileformat
    
    data['subalboption'] = subalboption
    data['subalb'] = subalb  
    data['subalbgridfile'] = subalbgridfile
    data['subalbgridfileformat'] = subalbgridfileformat
    
    data['subtypeoption'] = subtypeoption
    data['subtype'] = subtype  
    data['subtypegridfile'] = subtypegridfile
    data['subtypegridfileformat'] = subtypegridfileformat
    
    data['gsurfoption'] = gsurfoption
    data['gsurf'] = gsurf  
    data['gsurfgridfile'] = gsurfgridfile
    data['gsurfgridfileformat'] = gsurfgridfileformat
    
    data['ts_lastoption'] = tslastoption
    data['ts_last'] = tslast  
    data['ts_lastgridfile'] = tslastgridfile
    data['ts_lastgridfileformat'] = tslastgridfileformat
    
    for key in data:
        errors[key] = []
    
    context = {}   

    not_empty_check = tk.get_validator('not_empty') 
    actions = []
    if dfoption == 'Constant':
        actions.append(lambda: not_empty_check('df', data, errors, context))
        data['dfgridfile'] = None
    else:
        if data['dfgridfile'] == '0':  # value 0 if no file selected - Select a file...
            data['dfgridfile'] = None

        actions.append(lambda: not_empty_check('dfgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('dfgridfileformat', data, errors, context))

        # check if the file selected as drift factor file has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'dfgridfile', 'drift factor'))
        
    if aepoption == 'Constant':
        actions.append(lambda: not_empty_check('aep', data, errors, context))
        data['aepgridfile'] = None
    else:
        if data['aepgridfile'] == '0':
            data['aepgridfile'] = None

        actions.append(lambda: not_empty_check('aepgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('aepgridfileformat', data, errors, context))

        # check if the file selected as albedo extinction coefficient file has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'aepgridfile', 'albedo extinction coefficient'))
               
    if sbaroption == 'Constant':
        actions.append(lambda: not_empty_check('sbar', data, errors, context))
        data['sbargridfile'] = None
    else:
        if data['sbargridfile'] == '0':
            data['sbargridfile'] = None

        actions.append(lambda: not_empty_check('sbargridfile', data, errors, context))
        actions.append(lambda: not_empty_check('sbargridfileformat', data, errors, context))

        # check if the file selected as maximum snow load held per branch area file has already been
        # selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'sbargridfile',
                                                        'maximum snow load held per branch area'))
            
    if subalboption == 'Constant':
        actions.append(lambda: not_empty_check('subalb', data, errors, context))
        data['subalbgridfile'] = None
    else:
        if data['subalbgridfile'] == '0':
            data['subalbgridfile'] = None

        actions.append(lambda: not_empty_check('subalbgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('subalbgridfileformat', data, errors, context))

        # check if the file selected as albedo of the substrate beneath the snow file has already been
        # selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'subalbgridfile',
                                                        'albedo of the substrate beneath the snow'))
                  
    if subtypeoption == 'Constant':
        actions.append(lambda: not_empty_check('subtype', data, errors, context))
        data['subtypegridfile'] = None
    else:
        if data['subtypegridfile'] == '0':
            data['subtypegridfile'] = None

        actions.append(lambda: not_empty_check('subtypegridfile', data, errors, context)) 
        actions.append(lambda: not_empty_check('subtypegridfileformat', data, errors, context))

        # check if the file selected as type of beneath snow substrate encoded file has already been selected
        # for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'subtypegridfile',
                                                        'type of beneath snow substrate encoded'))
        
    if gsurfoption == 'Constant':
        actions.append(lambda: not_empty_check('gsurf', data, errors, context))
        data['gsurfgridfile'] = None
    else:
        if data['gsurfgridfile'] == '0':
            data['gsurfgridfile'] = None

        actions.append(lambda: not_empty_check('gsurfgridfile', data, errors, context))   
        actions.append(lambda: not_empty_check('gsurfgridfileformat', data, errors, context))

        # check if the file selected as fraction of surface snow melt file has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'gsurfgridfile', 'fraction of surface snow melt'))
       
    if tslastoption == 'Constant':
        actions.append(lambda: not_empty_check('ts_last', data, errors, context))
        data['ts_lastgridfile'] = None
    else:
        if data['ts_lastgridfile'] == '0':
            data['ts_lastgridfile'] = None

        actions.append(lambda: not_empty_check('ts_lastgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('ts_lastgridfileformat', data, errors, context))

        # check if the file selected as snow surface temp prior to one day of simulation start day file
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'ts_lastgridfile', 'snow surface temperature'))

    if form_stage not in session:
        session[form_stage] = {}

    session[form_stage] = data
    session.save()

    for action in actions:
        try:
            action()
        except:
            pass
        
    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value: # error message exists
            error_summary[key] = value

    tk.c.form_stage = form_stage
    stages = ['inactive', 'inactive', 'inactive', 'active', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_stage_five():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'stages': stages}
    form_stage = 'stage_5'
    
    ccoption = tk.request.params['ccoption']  
    cc = tk.request.params['cc']  
    ccgridfile = tk.request.params['ccgridfile']
    ccgridfileformat = tk.request.params['ccgridfileformat']
    
    hcanoption = tk.request.params['hcanoption']  
    hcan = tk.request.params['hcan']  
    hcangridfile = tk.request.params['hcangridfile']
    hcangridfileformat = tk.request.params['hcangridfileformat']
    
    laioption = tk.request.params['laioption']  
    lai = tk.request.params['lai']  
    laigridfile = tk.request.params['laigridfile']
    laigridfileformat = tk.request.params['laigridfileformat']
    
    ycageoption = tk.request.params['ycageoption']  
    ycage = tk.request.params['ycage']  
    ycagegridfile = tk.request.params['ycagegridfile']
    ycagegridfileformat = tk.request.params['ycagegridfileformat']
    
    data['ccoption'] = ccoption
    data['cc'] = cc  
    data['ccgridfile'] = ccgridfile
    data['ccgridfileformat'] = ccgridfileformat
    
    data['hcanoption'] = hcanoption
    data['hcan'] = hcan  
    data['hcangridfile'] = hcangridfile
    data['hcangridfileformat'] = hcangridfileformat
    
    data['laioption'] = laioption
    data['lai'] = lai  
    data['laigridfile'] = laigridfile
    data['laigridfileformat'] = laigridfileformat
    
    data['ycageoption'] = ycageoption
    data['ycage'] = ycage  
    data['ycagegridfile'] = ycagegridfile
    data['ycagegridfileformat'] = ycagegridfileformat
    
    for key in data:
        errors[key] = []
        
    context = {}   

    not_empty_check = tk.get_validator('not_empty') 
    actions = []

    if ccoption == 'NLCD':
        data['ccgridfile'] = None
    elif ccoption == 'Constant':
        actions.append(lambda: not_empty_check('cc', data, errors, context))
        data['ccgridfile'] = None
    elif ccoption == 'Grid':
        if data['ccgridfile'] == '0':  # value 0 if no file selected - Select a file...
            data['ccgridfile'] = None

        actions.append(lambda: not_empty_check('ccgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('ccgridfileformat', data, errors, context))

        # check if the file selected as canopy coverage file
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'ccgridfile', 'canopy coverage'))

    if hcanoption == 'NLCD':
        data['hcangridfile'] = None
    elif hcanoption == 'Constant':
        actions.append(lambda: not_empty_check('hcan', data, errors, context))
        data['hcangridfile'] = None
    elif hcanoption == 'Grid':
        if data['hcangridfile'] == '0':
            data['hcangridfile'] = None

        actions.append(lambda: not_empty_check('hcangridfile', data, errors, context))
        actions.append(lambda: not_empty_check('hcangridfileformat', data, errors, context))

        # check if the file selected for canopy height
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'hcangridfile', 'canopy height'))

    if laioption == 'NLCD':
        data['laigridfile'] = None
    elif laioption == 'Constant':
        actions.append(lambda: not_empty_check('lai', data, errors, context))
        data['laigridfile'] = None
    elif laioption == 'Grid':
        if data['laigridfile'] == '0':
            data['laigridfile'] = None

        actions.append(lambda: not_empty_check('laigridfile', data, errors, context))
        actions.append(lambda: not_empty_check('laigridfileformat', data, errors, context))    

        # check if the file selected for leaf area index
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'laigridfile', 'leaf area index'))

    if ycageoption == 'NLCD':
        data['ycagegridfile'] = None
    elif ycageoption == 'Constant':
        actions.append(lambda: not_empty_check('ycage', data, errors, context))
        data['ycagegridfile'] = None
    elif ycageoption == 'Grid':
        if data['ycagegridfile'] == '0':
            data['ycagegridfile'] = None

        actions.append(lambda: not_empty_check('ycagegridfile', data, errors, context))
        actions.append(lambda: not_empty_check('ycagegridfileformat', data, errors, context))

        # check if the file selected for forest age flag
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'ycagegridfile', 'forest age flag'))

    if form_stage not in session:
        session[form_stage] = {}

    session[form_stage] = data
    session.save()

    for action in actions:
        try:
            action()
        except:
            pass
        
    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value:   # error message exists
            error_summary[key] = value
    
    tk.c.form_stage = form_stage 
    stages = ['inactive', 'inactive', 'inactive', 'inactive', 'active', 'inactive', 'inactive', 'inactive', 'inactive']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_stage_six():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'stages': stages}
    form_stage = 'stage_6'
    
    aproption = tk.request.params['aproption']  
    apr = tk.request.params['apr']  
    aprgridfile = tk.request.params['aprgridfile']
    aprgridfileformat = tk.request.params['aprgridfileformat']
    
    slopeoption = tk.request.params['slopeoption']  
    slope = tk.request.params['slope']  
    slopegridfile = tk.request.params['slopegridfile']
    slopegridfileformat = tk.request.params['slopegridfileformat']
    
    aspectoption = tk.request.params['aspectoption']  
    aspect = tk.request.params['aspect']  
    aspectgridfile = tk.request.params['aspectgridfile']
    aspectgridfileformat = tk.request.params['aspectgridfileformat']
    
    latoption = tk.request.params['latitudeoption']  
    latitude = tk.request.params['latitude']  
    latitudegridfile = tk.request.params['latitudegridfile']
    latitudegridfileformat = tk.request.params['latitudegridfileformat']
    
    lonoption = tk.request.params['longitudeoption']  
    longitude = tk.request.params['longitude']  
    longitudegridfile = tk.request.params['longitudegridfile']
    longitudegridfileformat = tk.request.params['longitudegridfileformat']
    
    data['aproption'] = aproption
    data['apr'] = apr
    data['aprgridfile'] = aprgridfile
    data['aprgridfileformat'] = aprgridfileformat
    
    data['slopeoption'] = slopeoption
    data['slope'] = slope
    data['slopegridfile'] = slopegridfile
    data['slopegridfileformat'] = slopegridfileformat
    
    data['aspectoption'] = aspectoption
    data['aspect'] = aspect
    data['aspectgridfile'] = aspectgridfile
    data['aspectgridfileformat'] = aspectgridfileformat
    
    data['latitudeoption'] = latoption
    data['latitude'] = latitude
    data['latitudegridfile'] = latitudegridfile
    data['latitudegridfileformat'] = latitudegridfileformat
    
    data['longitudeoption'] = lonoption
    data['longitude'] = longitude
    data['longitudegridfile'] = longitudegridfile
    data['longitudegridfileformat'] = longitudegridfileformat
    
    for key in data:
        errors[key] = []
        
    context = {}   

    not_empty_check = tk.get_validator('not_empty') 
    actions = []

    if aproption == 'Compute':
        data['aprgridfile'] = None
    elif aproption == 'Constant':
        actions.append(lambda: not_empty_check('apr', data, errors, context))
        data['aprgridfile'] = None
    elif aproption == 'Grid':
        if data['aprgridfile'] == '0':  # value 0 if no file selected - Select a file...
            data['aprgridfile'] = None

        actions.append(lambda: not_empty_check('aprgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('aprgridfileformat', data, errors, context))

        # check if the file selected for average atmospheric pressure
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'aprgridfile', 'average atmospheric'))

    if slopeoption == 'Compute':
        data['slopegridfile'] = None
    elif slopeoption == 'Constant':
        actions.append(lambda: not_empty_check('slope', data, errors, context))
        data['slopegridfile'] = None
    elif slopeoption == 'Grid':
        if data['slopegridfile'] == '0':
            data['slopegridfile'] = None

        actions.append(lambda: not_empty_check('slopegridfile', data, errors, context))
        actions.append(lambda: not_empty_check('slopegridfileformat', data, errors, context))

        # check if the file selected for slope
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'slopegridfile', 'slope'))

    if aspectoption == 'Compute':
        data['aspectgridfile'] = None
    elif aspectoption == 'Constant':
        actions.append(lambda: not_empty_check('aspect', data, errors, context))
        data['aspectgridfile'] = None
    elif aspectoption == 'Grid':
        if data['aspectgridfile'] == '0':
            data['aspectgridfile'] = None

        actions.append(lambda: not_empty_check('aspectgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('aspectgridfileformat', data, errors, context))

        # check if the file selected for aspect
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'aspectgridfile', 'aspect'))

    if latoption == 'Compute':
        data['latitudegridfile'] = None
    elif latoption == 'Constant':
        actions.append(lambda: not_empty_check('latitude', data, errors, context))
        data['latitudegridfile'] = None
    elif latoption == 'Grid':
        if data['latitudegridfile'] == '0':
            data['latitudegridfile'] = None

        actions.append(lambda: not_empty_check('latitudegridfile', data, errors, context))
        actions.append(lambda: not_empty_check('latitudegridfileformat', data, errors, context))

        # check if the file selected for latitude
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'latitudegridfile', 'latitude'))

    if lonoption == 'Compute':
        data['longitudegridfile'] = None
    elif lonoption == 'Constant':
        actions.append(lambda: not_empty_check('longitude', data, errors, context))
        data['longitudegridfile'] = None
    elif lonoption == 'Grid':
        if data['longitudegridfile'] == '0':
            data['longitudegridfile'] = None

        actions.append(lambda: not_empty_check('longitudegridfile', data, errors, context))
        actions.append(lambda: not_empty_check('longitudegridfileformat', data, errors, context))

        # check if the file selected for longitude
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'longitudegridfile', 'longitude'))

    if form_stage not in session:
        session[form_stage] = {}

    session[form_stage] = data
    session.save()

    for action in actions:
        try:
            action()
        except:
            pass
        
    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value: # error message exists
            error_summary[key] = value
    
    tk.c.form_stage = form_stage 
    stages = ['inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'active', 'inactive', 'inactive', 'inactive']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_stage_seven():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary':error_summary, 'stages':stages}
    form_stage = 'stage_7'
    
    months = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september',
              'october', 'november', 'december']
    
    for month in months:
        temp_for_month = tk.request.params[month]  
        data[month] = temp_for_month
        errors[month] = []
            
    context = {}   
    if form_stage not in session:
        session[form_stage] = {}
         
    session[form_stage] = data    
    session.save()
          
    not_empty_check = tk.get_validator('not_empty') 

    for month in months:
        try:
            not_empty_check(month, data, errors, context)
        except:
            pass
        if len(errors[month]) == 0:
            # Check for data type numeric
            try:
                float(data[month])
            except ValueError:
                errors[month].append('Temperature should be a numeric value')
                   
    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value:   # error message exists
            error_summary[key] = value
    
    tk.c.form_stage = form_stage 
    stages = ['inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'active', 'inactive', 'inactive']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_stage_eight():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'stages': stages}
    form_stage = 'stage_8'
    
    tempoption = tk.request.params['taoption']  
    temperature = tk.request.params['ta']  
    temptextfile = tk.request.params['tatextfile']
    tempgridfile = tk.request.params['tagridfile']
    tempgridfileformat = tk.request.params['tagridfileformat']
    
    precoption = tk.request.params['precoption']  
    precipitation = tk.request.params['prec']  
    prectextfile = tk.request.params['prectextfile']
    precgridfile = tk.request.params['precgridfile']
    precgridfileformat = tk.request.params['precgridfileformat']
    
    windoption = tk.request.params['voption']  
    wind = tk.request.params['v']  
    windtextfile = tk.request.params['vtextfile']
    windgridfile = tk.request.params['vgridfile']
    windgridfileformat = tk.request.params['vgridfileformat']
    
    rhoption = tk.request.params['rhoption']  
    rh = tk.request.params['rh']  
    rhtextfile = tk.request.params['rhtextfile']
    rhgridfile = tk.request.params['rhgridfile']
    rhgridfileformat = tk.request.params['rhgridfileformat']
    
    snowalboption = tk.request.params['snowalboption']  
    snowalb = tk.request.params['snowalb']  
    snowalbtextfile = tk.request.params['snowalbtextfile']
    snowalbgridfile = tk.request.params['snowalbgridfile']
    snowalbgridfileformat = tk.request.params['snowalbgridfileformat']
    
    qgoption = tk.request.params['qgoption']  
    qg = tk.request.params['qg']  
    qgtextfile = tk.request.params['qgtextfile']
    qggridfile = tk.request.params['qggridfile']
    qggridfileformat = tk.request.params['qggridfileformat']
    
    data['taoption'] = tempoption
    data['ta'] = temperature
    data['tatextfile'] = temptextfile
    data['tagridfile'] = tempgridfile
    data['tagridfileformat'] = tempgridfileformat
    
    data['precoption'] = precoption
    data['prec'] = precipitation
    data['prectextfile'] = prectextfile
    data['precgridfile'] = precgridfile
    data['precgridfileformat'] = precgridfileformat
    
    data['voption'] = windoption
    data['v'] = wind
    data['vtextfile'] = windtextfile
    data['vgridfile'] = windgridfile
    data['vgridfileformat'] = windgridfileformat
    
    data['rhoption'] = rhoption
    data['rh'] = rh
    data['rhtextfile'] = rhtextfile
    data['rhgridfile'] = rhgridfile
    data['rhgridfileformat'] = rhgridfileformat
    
    data['snowalboption'] = snowalboption
    data['snowalb'] = snowalb
    data['snowalbtextfile'] = snowalbtextfile
    data['snowalbgridfile'] = snowalbgridfile
    data['snowalbgridfileformat'] = snowalbgridfileformat
    
    data['qgoption'] = qgoption
    data['qg'] = qg
    data['qgtextfile'] = qgtextfile
    data['qggridfile'] = qggridfile
    data['qggridfileformat'] = qggridfileformat
    
    for key in data:
        errors[key] = []
        
    context = {}   

    not_empty_check = tk.get_validator('not_empty') 
    actions = []

    if tempoption == 'Compute':
        data['tatextfile'] = None
        data['tagridfile'] = None
    elif tempoption == 'Constant':
        actions.append(lambda: not_empty_check('ta', data, errors, context))
        data['tatextfile'] = None
        data['tagridfile'] = None
    elif tempoption == 'Text':
        data['tagridfile'] = None
        if data['tatextfile'] == '0':  # value 0 represents the option- Select a a file..
            data['tatextfile'] = None

        actions.append(lambda: not_empty_check('tatextfile', data, errors, context))

        # check if the file selected for temp
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'tatextfile', 'temperature'))

    elif tempoption == 'Grid':
        data['tatextfile'] = None
        if data['tagridfile'] == '0':
            data['tagridfile'] = None

        actions.append(lambda: not_empty_check('tagridfile', data, errors, context))
        actions.append(lambda: not_empty_check('tagridfileformat', data, errors, context))

        # check if the file selected for temperature
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'tagridfile', 'temperature'))

    if precoption == 'Compute':
        data['prectextfile'] = None
        data['precgridfile'] = None
    elif precoption == 'Constant':
        actions.append(lambda: not_empty_check('prec', data, errors, context))
        data['prectextfile'] = None
        data['precgridfile'] = None
    elif precoption == 'Text':
        data['precgridfile'] = None
        if data['prectextfile'] == '0':
            data['prectextfile'] = None

        actions.append(lambda: not_empty_check('prectextfile', data, errors, context))

        # check if the file selected for precipitation
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'prectextfile', 'precipitation'))

    elif precoption == 'Grid':
        data['prectextfile'] = None
        if data['precgridfile'] == '0':
            data['precgridfile'] = None

        actions.append(lambda: not_empty_check('precgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('precgridfileformat', data, errors, context))

        # check if the file selected for precipitation
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'precgridfile', 'precipitation'))

    if windoption == 'Compute':
        data['vtextfile'] = None
        data['vgridfile'] = None
    elif windoption == 'Constant':
        actions.append(lambda: not_empty_check('v', data, errors, context))
        data['vtextfile'] = None
        data['vgridfile'] = None
    elif windoption == 'Text':
        data['vgridfile'] = None
        if data['vtextfile'] == '0':
            data['vtextfile'] = None

        actions.append(lambda: not_empty_check('vtextfile', data, errors, context))

        # check if the file selected for wind
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'vtextfile', 'wind'))

    elif windoption == 'Grid':
        data['vtextfile'] = None
        if data['vgridfile'] == '0':
            data['vgridfile'] = None

        actions.append(lambda: not_empty_check('vgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('vgridfileformat', data, errors, context))

        # check if the file selected for wind
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'vgridfile', 'wind'))

    if rhoption == 'Compute':
        data['rhtextfile'] = None
        data['rhgridfile'] = None
    elif rhoption == 'Constant':
        actions.append(lambda: not_empty_check('rh', data, errors, context))
        data['rhtextfile'] = None
        data['rhgridfile'] = None
    elif rhoption == 'Text':
        data['rhgridfile'] = None
        if data['rhtextfile'] == '0':
            data['rhtextfile'] = None

        actions.append(lambda: not_empty_check('rhtextfile', data, errors, context))

        # check if the file selected for rh
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'rhtextfile', 'relative humidity'))

    elif rhoption == 'Grid':
        data['rhtextfile'] = None
        if data['rhgridfile'] == '0':
            data['rhgridfile'] = None

        actions.append(lambda: not_empty_check('rhgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('rhgridfileformat', data, errors, context))

        # check if the file selected for rh
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'rhgridfile', 'relative humidity'))

    if snowalboption == 'Compute':
        data['snowalbtextfile'] = None
        data['snowalbgridfile'] = None
    elif snowalboption == 'Constant':
        actions.append(lambda: not_empty_check('snowalb', data, errors, context))
        data['snowalbtextfile'] = None
        data['snowalbgridfile'] = None
    elif snowalboption == 'Text':
        data['snowalbgridfile'] = None
        if data['snowalbtextfile'] == '0':
            data['snowalbtextfile'] = None

        actions.append(lambda: not_empty_check('snowalbtextfile', data, errors, context))

        # check if the file selected for snow albedo
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'snowalbtextfile', 'snow albedo'))

    elif snowalboption == 'Grid':
        data['snowalbtextfile'] = None
        if data['snowalbgridfile'] == '0':
            data['snowalbgridfile'] = None

        actions.append(lambda: not_empty_check('snowalbgridfile', data, errors, context))
        actions.append(lambda: not_empty_check('snowalbgridfileformat', data, errors, context))

        # check if the file selected for snow albedo
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'snowalbgridfile', 'snow albedo'))

    if qgoption == 'Constant':
        actions.append(lambda: not_empty_check('qg', data, errors, context))
        data['qgtextfile'] = None
        data['qggridfile'] = None
    elif qgoption == 'Text':
        data['qggridfile'] = None
        if data['qgtextfile'] == '0':
            data['qgtextfile'] = None

        actions.append(lambda: not_empty_check('qgtextfile', data, errors, context))

        # check if the file selected for ground heat flux
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'qgtextfile', 'ground heat flux'))

    elif qgoption == 'Grid':
        data['qgtextfile'] = None
        if data['qggridfile'] == '0':
            data['qggridfile'] = None

        actions.append(lambda: not_empty_check('qggridfile', data, errors, context))
        actions.append(lambda: not_empty_check('qggridfileformat', data, errors, context))

        # check if the file selected for ground heat flux
        # has already been selected for any other input
        actions.append(lambda: _validate_file_selection(data, errors, 'qggridfile', 'ground heat flux'))

    if form_stage not in session:
        session[form_stage] = {}

    session[form_stage] = data
    session.save()

    for action in actions:
        try:
            action()
        except:
            pass
        
    #check for constant value if exits that they are numeric type    
    if tempoption == 'Constant' and len(errors['ta']) == 0:
        try:
            float(data['ta'])
        except ValueError:
            errors['ta'].append('Temperature should be a numeric value')
    
    if precoption == 'Constant' and len(errors['prec']) == 0:
        try:
            float(data['prec'])
        except ValueError:
            errors['prec'].append('Precipitation should be a numeric value')
                 
    if windoption == 'Constant' and len(errors['v']) == 0:
        try:
            float(data['v'])
        except ValueError:
            errors['v'].append('Wind speed should be a numeric value')
                 
    if rhoption == 'Constant' and len(errors['rh']) == 0:
        try:
            float(data['rh'])
        except ValueError:
            errors['rh'].append('Relative humidity should be a numeric value')
                 
    if snowalboption == 'Constant' and len(errors['snowalb']) == 0:
        try:
            float(data['snowalb'])
        except ValueError:
            errors['snowalb'].append('Snow albedo should be a numeric value')
                 
    if qgoption == 'Constant' and len(errors['qg']) == 0:
        try:
            float(data['qg'])
        except ValueError:
            errors['qg'].append('Ground heat flux should be a numeric value')
                 
    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value: # error message exists
            error_summary[key] = value
    
    tk.c.form_stage = form_stage 
    stages = ['inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'active', 'inactive']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_stage_nine():
    session = base.session
    errors = {}
    data = {}
    error_summary = {}
    stages = []
    form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary, 'stages': stages}
    form_stage = 'stage_9' 
    
    outputControlFileOption = tk.request.params['outputControlFileOption']  
    outputControlFile = tk.request.params['outputControlFile']  
    aggrOutputControlFileOption = tk.request.params['aggrOutputControlFileOption']  
    aggrOutputControlFile = tk.request.params['aggrOutputControlFile']      
    
    data['outputControlFileOption'] = outputControlFileOption
    data['outputControlFile'] = outputControlFile   
    data['aggrOutputControlFileOption'] = aggrOutputControlFileOption
    data['aggrOutputControlFile'] = aggrOutputControlFile   
    
    for key in data:
        errors[key] = []
        
    context = {}   
    if form_stage not in session:
        session[form_stage] = {}
         
    session[form_stage] = data    
    session.save()
    
    not_empty_check = tk.get_validator('not_empty')   # not_empty(key, data, errors, context):
           
    if outputControlFileOption == 'No':
        if data['outputControlFile'] == '0':
            data['outputControlFile'] = None
        try:
            not_empty_check('outputControlFile', data, errors, context)
        except:
           pass

        # check if the file selected for output control file
        # has already been selected for any other input
        _validate_file_selection(data, errors, 'outputControlFile', 'output control')
    else:
        data['outputControlFile'] = None

    if aggrOutputControlFileOption == 'No':
        if data['aggrOutputControlFile'] == '0':
            data['aggrOutputControlFile'] = None

        try:
            not_empty_check('aggrOutputControlFile', data, errors, context)
        except:
           pass

        # check if the file selected for aggregated output control
        # has already been selected for any other input
        _validate_file_selection(data, errors, 'aggrOutputControlFile', 'aggregated output control')
    else:
        data['aggrOutputControlFile'] = None

    for key in errors:
        # Get the error message for the form field (key)
        value = errors.get(key)            
        if value: # error message exists
            error_summary[key] = value
    
    tk.c.form_stage = form_stage 
    stages = ['inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'inactive', 'active']
    form_vars['data'] = data
    form_vars['stages'] = stages
    form_vars['errors'] = errors
    form_vars['error_summary'] = error_summary
    return form_vars


def _validate_file_selection(data, errors, file_form_field_name, file_name):
    session = base.session
    for frm_stage in session:
        if frm_stage not in ['stage_1', 'stage_2', 'stage_3', 'stage_4', 'stage_5', 'stage_6', 'stage_7',
                             'stage_8', 'stage_9']:
            continue

        form_stage_data = session[frm_stage]
        for key, value in form_stage_data.items():
            if value == '0' or not value:  # no file selected
                continue
            if key == file_form_field_name:
                continue
            if data[file_form_field_name] == value:
                errors[file_form_field_name].append('The file you have selected as %s file is already '
                                                    'selected for another input.' % file_name)
                return


def _get_default_data(form_stage):        
    if form_stage == 'stage_2':
        return _get_default_data_stage_two()
    elif form_stage == 'stage_3':
        return _get_default_data_stage_three()
    elif form_stage == 'stage_4':
        return _get_default_data_stage_four()
    elif form_stage == 'stage_5':
        return _get_default_data_stage_five()
    elif form_stage == 'stage_6':
        return _get_default_data_stage_six()
    elif form_stage == 'stage_7':
        return _get_default_data_stage_seven()
    elif form_stage == 'stage_8':
        return _get_default_data_stage_eight()
    elif form_stage == 'stage_9':
        return _get_default_data_stage_nine()


def _get_default_data_stage_two():
    data = {'parametersfileoption': 'Yes'}
    return data


def _get_default_data_stage_three():
    # TODO: read these hard coded values from a file that can exist in the UEB Input Dataset
    data = {}
    data['usicoption'] = 'Constant'
    data['usic'] = 0
    data['wsisoption'] = 'Constant'
    data['wsis'] = 0
    data['ticoption'] = 'Constant'
    data['tic'] = 0
    data['wcicoption'] = 'Constant'
    data['wcic'] = 0    
    return data


def _get_default_data_stage_four():
    # TODO: read these hard coded values from a file that can exist in the UEB Input Dataset
    data = {}
    data['dfoption'] = 'Constant'
    data['df'] = 1
    data['aepoption'] = 'Constant'
    data['aep'] = 0.1
    data['sbaroption'] = 'Constant'
    data['sbar'] = 6.6
    data['subalboption'] = 'Constant'
    data['subalb'] = 0.25
    data['subtypeoption'] = 'Constant'
    data['subtype'] = 0
    data['gsurfoption'] = 'Constant'
    data['gsurf'] = 0
    data['ts_lastoption'] = 'Constant'
    data['ts_last'] = -9999    
    return data


def _get_default_data_stage_five():
    data = {}
    data['ccoption'] = 'NLCD'
    data['hcanoption'] = 'NLCD'
    data['laioption'] = 'NLCD'
    data['ycageoption'] = 'NLCD'    
    return data


def _get_default_data_stage_six():
    data = {}
    data['aproption'] = 'Compute'
    data['slopeoption'] = 'Compute'
    data['aspectoption'] = 'Compute'
    data['latitudeoption'] = 'Compute'    
    data['longitudeoption'] = 'Compute'
    return data

def _get_default_data_stage_seven():
    # TODO: read these hard coded values from a file that can exist in the UEB Input Dataset
    data = {}
    data['january'] = 6.743
    data['february'] = 7.927
    data['march'] = 8.055
    data['april'] = 8.602  
    data['may'] = 8.43
    data['june'] = 9.76
    data['july'] = 0
    data['august'] = 0
    data['september'] = 0
    data['october'] = 7.4
    data['november'] = 9.14
    data['december'] = 6.67
    return data


def _get_default_data_stage_eight():
    data = {}
    data['taoption'] = 'Compute'
    data['precoption'] = 'Compute'
    data['voption'] = 'Compute'
    data['rhoption'] = 'Compute'
    data['snowalboption'] = 'Compute'
    data['qgoption'] = 'Constant'
    data['qg'] = 0
    return data


def _get_default_data_stage_nine():
    data = {}
    data['outputControlFileOption'] = 'Yes'
    data['aggrOutputControlFileOption'] = 'Yes'
    return data


def _get_predefined_name(predefined_name_key):
    predefined_names = {}
    predefined_names['ckan_user_session_temp_dir'] = '/tmp/ckan'
    predefined_names['ueb_request_json_file_name'] = 'ueb_pkg_request.json'
    predefined_names['ueb_request_text_resource_file_name'] = 'ueb_pkg_request.txt'
    predefined_names['ueb_request_zip_file_name'] = 'ueb_request.zip'
    
    return predefined_names.get(predefined_name_key, None)


def _get_package_request_in_json_format():
    # TODO: Note that the session object may not have data for all stages of the 
    # form if the user did not navigate to all stages. Prior to accessing data for a stage
    # from the session object, check that the data for the specific stage exits in session
    # object, otherwise implement a method to get default data for any give stage of the form 
    selected_file_ids = {}    
    ueb_request_data = {}
    session = base.session    
    tk.c.ueb_input_sections = []
    tk.c.ueb_input_section_data_items = {}
    
    ueb_default_dataset = _get_package('ueb-default-configuration-dataset')
    ueb_default_input_dataset_id = ueb_default_dataset['id']    # '0e39dd8f-85ac-4bee-b18c-ac5cb7d60328'
    
    stage_1_data = session['stage_1']
    section_name = 'Model domain setup'
    tk.c.ueb_input_sections.append(section_name)
    #tk.c.ueb_input_section_data_items.append('Set package')
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = ['Start date:', 'End date:', 'Time step:',
                                                                'Buffer size:', 'Grid cell size:', 'Domain file name:']
    
    tk.c.ueb_input_section_data_items[section_name]['Start date:'] = stage_1_data['startdate']    
    ueb_request_data['StartDate'] = stage_1_data['startdate']
    
    tk.c.ueb_input_section_data_items[section_name]['End date:'] = stage_1_data['enddate']  
    ueb_request_data['EndDate'] = stage_1_data['enddate']
    
    tk.c.ueb_input_section_data_items[section_name]['Time step:'] = stage_1_data['timestep']  
    ueb_request_data['TimeStep'] = stage_1_data['timestep']
    
    tk.c.ueb_input_section_data_items[section_name]['Buffer size:'] = stage_1_data['buffersize']  
    ueb_request_data['BufferSize'] = stage_1_data['buffersize']
    
    tk.c.ueb_input_section_data_items[section_name]['Grid cell size:'] = stage_1_data['gridcellsize']  
    ueb_request_data['GridCellSize'] = stage_1_data['gridcellsize']
    
    if stage_1_data['domainfiletypeoption'] == 'polygon':
        ueb_request_data['DomainFileName'] = _get_file_name_from_file_id(stage_1_data['domainshapefile'])
        selected_file_ids['domain_file_id'] = stage_1_data['domainshapefile']
    else:
        ueb_request_data['DomainFileName'] = _get_file_name_from_file_id(stage_1_data['domainnetcdffile'])
        ueb_request_data['DomainGridFileFormat'] = stage_1_data['domainnetcdffileformat']
        selected_file_ids['domain_file_id'] = stage_1_data['domainnetcdffile']
   
    tk.c.ueb_input_section_data_items[section_name]['Domain file name:'] = ueb_request_data['DomainFileName'] 
       
    stage_2_data = session.get('stage_2', None)
    section_name = 'Model parameters setup'
    tk.c.ueb_input_sections.append(section_name)    
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = []
    tk.c.ueb_input_section_data_items[section_name]['order'].append('Use default parameter file:')
    if not stage_2_data:
        # get the default data
        stage_2_data = _get_default_data_stage_two()
       
    default_parameter_file_name = 'param.dat'
    if stage_2_data['parametersfileoption'] == 'Yes':       
        selected_file_ids['parameters_file_id'] = _get_file_id_from_file_name(ueb_default_input_dataset_id,
                                                                              default_parameter_file_name)
        ueb_request_data['ModelParametersFileName'] = default_parameter_file_name
        tk.c.ueb_input_section_data_items[section_name]['Use default parameter file:'] = 'Yes'
    else:
        selected_file_ids['parameters_file_id'] = stage_2_data['parametersfile']
        ueb_request_data['ModelParametersFileName'] = _get_file_name_from_file_id(selected_file_ids['parameters_file_id'])
        tk.c.ueb_input_section_data_items[section_name]['Use default parameter file:'] = 'No' 
        tk.c.ueb_input_section_data_items[section_name]['Parameter file name:'] = \
            ueb_request_data['ModelParametersFileName']
        tk.c.ueb_input_section_data_items[section_name]['order'].append('Parameter file name:')

    stage_3_data = session.get('stage_3', None)
    if not stage_3_data:
        # get the default data
        stage_3_data = _get_default_data_stage_three()
       
    ueb_request_data['SiteInitialConditions'] = {}
    section_name = 'Site initial condition - state variables setup'
    tk.c.ueb_input_sections.append(section_name)    
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = []
    
    stage_3_variables = ['usic', 'wsis', 'tic', 'wcic']
    for var in stage_3_variables:    
        ueb_request_data['SiteInitialConditions']['is_' + var + '_constant'] = False    
        ueb_request_data['SiteInitialConditions'][var + '_constant_value'] = 0
        ueb_request_data['SiteInitialConditions'][var + '_grid_file_name'] = ''
        ueb_request_data['SiteInitialConditions'][var + '_grid_file_format'] = ''
        if stage_3_data[var + 'option'] == 'Constant':
            ueb_request_data['SiteInitialConditions']['is_' + var + '_constant'] = True
            ueb_request_data['SiteInitialConditions'][var + '_constant_value'] = stage_3_data[var]  
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'Yes '    
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-constant value:'] = stage_3_data[var]  
        else:       
            selected_file_ids[var + '_grid_file_id'] = stage_3_data[var + 'gridfile']  
            ueb_request_data['SiteInitialConditions'][var + '_grid_file_name'] = _get_file_name_from_file_id(
                stage_3_data[var + 'gridfile'])
            ueb_request_data['SiteInitialConditions'][var + '_grid_file_format'] = stage_3_data[var + 'gridfileformat']
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'No '
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file name:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] = \
                ueb_request_data['SiteInitialConditions'][var + '_grid_file_name']
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file format:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] = \
                stage_3_data[var + 'gridfileformat']

    stage_4_data = session.get('stage_4', None)
    if not stage_4_data:
        # get the default data
        stage_4_data =  _get_default_data_stage_four()
    
    section_name = 'Site initial condition - snow variables setup'
    tk.c.ueb_input_sections.append(section_name)    
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = []
        
    stage_4_variables = ['df', 'aep', 'sbar', 'subalb', 'subtype', 'gsurf', 'ts_last']
    for var in stage_4_variables:
        ueb_request_data['SiteInitialConditions']['is_' + var + '_constant'] = False    
        ueb_request_data['SiteInitialConditions'][var + '_constant_value'] = 0
        ueb_request_data['SiteInitialConditions'][var + '_grid_file_name'] = ''
        ueb_request_data['SiteInitialConditions'][var + '_grid_file_format'] = ''
        if stage_4_data[var + 'option'] == 'Constant':
            ueb_request_data['SiteInitialConditions']['is_' + var + '_constant'] = True
            ueb_request_data['SiteInitialConditions'][var + '_constant_value'] = stage_4_data[var]  
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'Yes ' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-constant value:'] = stage_4_data[var]  
                   
        else:        
            selected_file_ids[var + '_grid_file_id'] = stage_4_data[var + 'gridfile']  
            ueb_request_data['SiteInitialConditions'][var + '_grid_file_name'] = \
                _get_file_name_from_file_id(stage_4_data[var + 'gridfile'])
            ueb_request_data['SiteInitialConditions'][var + '_grid_file_format'] = \
                stage_4_data[var + 'gridfileformat']
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'No '
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file name:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] =\
                ueb_request_data['SiteInitialConditions'][var + '_grid_file_name']
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file format:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] =\
                stage_4_data[var + 'gridfileformat']

    stage_5_data = session.get('stage_5', None)
    if not stage_5_data:
        # get the default data
        stage_5_data = _get_default_data_stage_five()
    
    # set data for confirmation page
    section_name = 'Site initial condition - land cover variables setup'
    tk.c.ueb_input_sections.append(section_name)    
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = []
       
    stage_5_variables = ['cc', 'hcan', 'lai', 'ycage']
    for var in stage_5_variables:        
        ueb_request_data['SiteInitialConditions'][var + '_constant_value'] = 0
        ueb_request_data['SiteInitialConditions'][var + '_grid_file_name'] = ''
        ueb_request_data['SiteInitialConditions'][var + '_grid_file_format'] = ''
        ueb_request_data['SiteInitialConditions']['is_' + var + '_constant'] = False  
        ueb_request_data['SiteInitialConditions']['is_' + var + '_derive_from_NLCD'] = False
    
        if stage_5_data[var + 'option'] == 'Constant':
            ueb_request_data['SiteInitialConditions']['is_' + var + '_constant'] = True        
            ueb_request_data['SiteInitialConditions'][var + '_constant_value'] = stage_5_data[var]
            # set data for confirmation page
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:')             
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'Yes ' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-constant value:'] = stage_5_data[var]  
        elif stage_5_data[var + 'option'] == 'NLCD':
            ueb_request_data['SiteInitialConditions']['is_' + var + '_derive_from_NLCD'] = True  
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-derive from NLCD:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-derive from NLCD:'] = 'Yes '             
        else:        
            selected_file_ids[var + '_grid_file_id'] = stage_5_data[var + 'gridfile']  
            ueb_request_data['SiteInitialConditions'][var + '_grid_file_name'] = \
                _get_file_name_from_file_id(stage_5_data[var + 'gridfile'])
            ueb_request_data['SiteInitialConditions'][var + '_grid_file_format'] = stage_5_data[var + 'gridfileformat']
            # set data for confirmation page
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'No ' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-derive from NLCD:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-derive from NLCD:'] = 'No ' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file name:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] = \
                ueb_request_data['SiteInitialConditions'][var + '_grid_file_name']
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file format:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] = \
                stage_5_data[var + 'gridfileformat']

    stage_6_data = session.get('stage_6', None)
    if not stage_6_data:
        # get the default data
        stage_6_data = _get_default_data_stage_six()
    
    # set data for confirmation page
    section_name = 'Site initial condition - geographic variables setup'
    tk.c.ueb_input_sections.append(section_name)    
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = []
    
    stage_6_variables = ['apr', 'slope', 'aspect', 'latitude', 'longitude']
    for var in stage_6_variables:        
        ueb_request_data['SiteInitialConditions'][var + '_constant_value'] = 0
        ueb_request_data['SiteInitialConditions'][var + '_grid_file_name'] = ''
        ueb_request_data['SiteInitialConditions'][var + '_grid_file_format'] = ''
        ueb_request_data['SiteInitialConditions']['is_' + var + '_constant'] = False 
        if var == 'latitude' or var == 'longitude':
            ueb_request_data['SiteInitialConditions']['is_' + var + '_derive_from_projection'] = False
        else:
            ueb_request_data['SiteInitialConditions']['is_' + var + '_derive_from_elevation'] = False
    
        if stage_6_data[var + 'option'] == 'Constant':
            ueb_request_data['SiteInitialConditions']['is_' + var + '_constant'] = True        
            ueb_request_data['SiteInitialConditions'][var + '_constant_value'] = stage_6_data[var]
            # set data for confirmation page
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:')             
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'Yes ' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-constant value:'] = stage_6_data[var] 
        elif stage_6_data[var + 'option'] == 'Compute':
            if var == 'latitude' or var == 'longitude':
                ueb_request_data['SiteInitialConditions']['is_' + var + '_derive_from_projection'] = True  
            else:
                ueb_request_data['SiteInitialConditions']['is_' + var + '_derive_from_elevation'] = True  
            
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-derive from domain elevation data:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-derive from domain elevation data:'] = 'Yes '              
        else:        
            selected_file_ids[var + '_grid_file_id'] = stage_6_data[var + 'gridfile']  
            ueb_request_data['SiteInitialConditions'][var + '_grid_file_name'] = \
                _get_file_name_from_file_id(stage_6_data[var + 'gridfile'])
            ueb_request_data['SiteInitialConditions'][var + '_grid_file_format'] = stage_6_data[var + 'gridfileformat']
            # set data for confirmation page
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'No ' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-derive from elevation data:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-derive from elevation data:'] = 'No ' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file name:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] = \
                ueb_request_data['SiteInitialConditions'][var + '_grid_file_name']
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file format:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] =\
                stage_6_data[var + 'gridfileformat']

    stage_7_data = session.get('stage_7', None)
    if not stage_7_data:
        # get the default data
        stage_7_data = _get_default_data_stage_seven()
    
    # set data for confirmation page
    section_name = 'Site initial condition - monthly mean dirunal temperature setup'
    tk.c.ueb_input_sections.append(section_name)    
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = []
       
    ueb_request_data['BristowCambellBValues'] = {}
    for key_month, value_temp in stage_7_data.items():
        var = 'b' + _convert_month_name_to_month_number(key_month)
        ueb_request_data['BristowCambellBValues'][var] = value_temp
    
    month_names = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                   'October', 'November', 'December']
    months_dict = {
                'January': '01',
                'February': '02',
                'March': '03',
                'April': '04',
                'May': '05',
                'June': '06',
                'July': '07',
                'August': '08',
                'September': '09',
                'October': '10',
                'November': '11',
                'December': '12'
            }
    for month in month_names:
        var = 'b' + months_dict[month]
        tk.c.ueb_input_section_data_items[section_name]['order'].append(month + ':') 
        tk.c.ueb_input_section_data_items[section_name][month + ':'] = ueb_request_data['BristowCambellBValues'][var]

    stage_8_data = session.get('stage_8', None)
    if not stage_8_data:
        # get the default data
        stage_8_data = _get_default_data_stage_eight()
    
    # set data for confirmation page
    section_name = 'Time series variables setup'
    tk.c.ueb_input_sections.append(section_name)    
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = []
       
    ueb_request_data['TimeSeriesInputs'] = {}
    stage_8_variables = ['ta', 'prec', 'v', 'rh', 'snowalb', 'qg']
    
    for var in stage_8_variables:
        ueb_request_data['TimeSeriesInputs'][var + '_constant_value'] = 0
        ueb_request_data['TimeSeriesInputs'][var + '_text_file_name'] = ''
        ueb_request_data['TimeSeriesInputs'][var + '_grid_file_name'] = ''
        ueb_request_data['TimeSeriesInputs'][var + '_grid_file_format'] = ''
        ueb_request_data['TimeSeriesInputs']['is_' + var + '_constant'] = False  
        
        tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-compute:')        
        if var != 'qg':
            ueb_request_data['TimeSeriesInputs']['is_' + var + '_compute'] = False
            # set data for confirmation page                 
            tk.c.ueb_input_section_data_items[section_name][var + '-compute:'] = 'No' 
            
        if stage_8_data[var + 'option'] == 'Constant':
            ueb_request_data['TimeSeriesInputs']['is_' + var + '_constant'] = True        
            ueb_request_data['TimeSeriesInputs'][var + '_constant_value'] = stage_8_data[var]
            tk.c.ueb_input_section_data_items[section_name][var + '-compute:'] = 'No' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'Yes' 
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-constant value:'] = stage_8_data[var] 
            
        elif stage_8_data[var + 'option'] == 'Compute':
            ueb_request_data['TimeSeriesInputs']['is_' + var + '_compute'] = True 
            tk.c.ueb_input_section_data_items[section_name][var + '-compute:'] = 'Yes' 
        elif stage_8_data[var + 'option'] == 'Text': 
            selected_file_ids[var + '_text_file_id'] = stage_8_data[var + 'textfile']  
            ueb_request_data['TimeSeriesInputs'][var + '_text_file_name'] = \
                _get_file_name_from_file_id(stage_8_data[var + 'textfile'])
            tk.c.ueb_input_section_data_items[section_name][var + '-compute:'] = 'No'             
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use constant value:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use constant value:'] = 'No'  
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use an input text file:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use an input text file:'] = 'Yes'  
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-text file name:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-text file name:'] = \
                ueb_request_data['TimeSeriesInputs'][var + '_text_file_name']
                    
        else:        
            selected_file_ids[var + '_grid_file_id'] = stage_8_data[var + 'gridfile']  
            ueb_request_data['TimeSeriesInputs'][var + '_grid_file_name'] = \
                _get_file_name_from_file_id(stage_8_data[var + 'gridfile'])
            ueb_request_data['TimeSeriesInputs'][var + '_grid_file_format'] = stage_8_data[var + 'gridfileformat']
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-use a input grid file:') 
            tk.c.ueb_input_section_data_items[section_name][var + '-use a input grid file:'] = 'Yes'  
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file name:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] =\
                ueb_request_data['TimeSeriesInputs'][var + '_grid_file_name']
            tk.c.ueb_input_section_data_items[section_name]['order'].append(var + '-grid file format:')  
            tk.c.ueb_input_section_data_items[section_name][var + '-grid file name:'] =\
                stage_8_data[var + 'gridfileformat']

    stage_9_data = session.get('stage_9', None)
    if not stage_9_data:
        # get the default data
        stage_9_data = _get_default_data_stage_nine()
    # set data for confirmation page
    section_name = 'Output variables setup'
    tk.c.ueb_input_sections.append(section_name)    
    tk.c.ueb_input_section_data_items[section_name] = {}
    tk.c.ueb_input_section_data_items[section_name]['order'] = []
       
    default_output_control_file_name = 'outputcontrol.dat'
    default_aggr_output_control_file_name = 'aggregatedoutputcontrol.dat'
    tk.c.ueb_input_section_data_items[section_name]['order'].append('Use default output control file:') 
    tk.c.ueb_input_section_data_items[section_name]['order'].append('Use default aggregated output control file:') 
    
    if stage_9_data['outputControlFileOption'] == 'Yes':
        selected_file_ids['outputcontrol_file_id'] = _get_file_id_from_file_name(ueb_default_input_dataset_id,
                                                                                 default_output_control_file_name)
        ueb_request_data['OutputControlFileName'] = default_output_control_file_name
        tk.c.ueb_input_section_data_items[section_name]['Use default output control file:'] = 'Yes'
    else:
        selected_file_ids['outputcontrol_file_id'] = stage_9_data['outputControlFile']
        ueb_request_data['OutputControlFileName'] =\
            _get_file_name_from_file_id(selected_file_ids['outputcontrol_file_id'])
        tk.c.ueb_input_section_data_items[section_name]['Use default output control file:'] = 'No' 
        tk.c.ueb_input_section_data_items[section_name]['order'].append('Output control file name:')  
        tk.c.ueb_input_section_data_items[section_name]['Output control file name:'] =\
            ueb_request_data['OutputControlFileName']
    
    if stage_9_data['aggrOutputControlFileOption'] == 'Yes':
        selected_file_ids['aggroutputcontrol_file_id'] = _get_file_id_from_file_name(
            ueb_default_input_dataset_id, default_aggr_output_control_file_name)
        ueb_request_data['AggregatedOutputControlFileName'] = default_aggr_output_control_file_name
        tk.c.ueb_input_section_data_items[section_name]['Use default aggregated output control file:'] = 'Yes'
    else:
        selected_file_ids['aggroutputcontrol_file_id'] = stage_9_data['aggrOutputControlFile'] 
        ueb_request_data['AggregatedOutputControlFileName'] = _get_file_name_from_file_id(
            selected_file_ids['aggroutputcontrol_file_id'])
        tk.c.ueb_input_section_data_items[section_name]['Use default aggregated output control file:'] = 'Yes'
        tk.c.ueb_input_section_data_items[section_name]['order'].append('Aggregated output control file name:')  
        tk.c.ueb_input_section_data_items[section_name]['Aggregated output control file name:'] =\
            ueb_request_data['AggregatedOutputControlFileName']
       
    ueb_req_json = json.dumps(ueb_request_data)
    ueb_request = {'selected_file_ids': selected_file_ids, 'ueb_req_json': ueb_req_json}
    return ueb_request


def _convert_month_name_to_month_number(month):
    months = {'january': '01', 'february': '02', 'march': '03', 'april': '04', 'may': '05', 'june': '06', 'july': '07',
              'august': '08', 'september': '09', 'october': '10', 'november': '11', 'december': '12' }
    return months.get(month, '00')


def _save_ueb_request_as_dataset(pkgname, selected_file_ids, selected_user_org):
    """
    create a new ckan package/datatset of dataset type 'model-configuration'
    with package title as the name of the ueb model package request
    save the package request information from the c object to a text file to a temporary dir
    and then add the file as a resource to the package created.    Also add all other files
    selected as inputs to build package as a resource in the same dataset

    param pkgname: name of the package as entered by the user
    param selected_file_ids: a dict object containing name of files with their corresponding resource ids
    param selected_user_org: id of the user selected organization for which a new dataset will be created
    return: id of the new dataset that was created or None
    """
    source = 'uebpackage.packagecreate._save_ueb_request_as_dataset():'

    ckan_default_dir = uebhelper.StringSettings.ckan_user_session_temp_dir
    # create a directory for saving the file
    # this will be a dir in the form of: /tmp/ckan/{session id}/files
    #destination_dir = os.path.join(ckan_default_dir, base.session.id, 'files')
    try:
        destination_dir = os.path.join(ckan_default_dir, base.session.id)
        if os.path.isdir(destination_dir):
            shutil.rmtree(destination_dir)
        os.makedirs(destination_dir)
    except Exception as e:
        log.error(source + 'Failed to create temporary dir for shapefile: %s \n Exception: %s' % (destination_dir, e))
        return None

    ueb_request_text_file_name = uebhelper.StringSettings.ueb_request_text_resource_file_name
    request_resource_file = os.path.join(destination_dir, ueb_request_text_file_name)

    try:
        with open(request_resource_file, 'w') as file_obj:
            for section in tk.c.ueb_input_sections:
                file_obj.write(section + ':\n')
                section_data_items = tk.c.ueb_input_section_data_items[section]
                for key in section_data_items['order']:
                    data_item_line_to_write = '\t' + key + '%s' % section_data_items[key] + '\n'
                    file_obj.write(data_item_line_to_write)

                file_obj.write('\n')
    except Exception as e:
        log.error(source + 'Failed to save the ueb_package request file to temporary location'
                           ' for package: %s \n Exception: %s' % (pkgname, e))
        return None

    # create a package
    package_create_action = tk.get_action('package_create')

    # create unique package name using the current time stamp as a postfix to any package name
    unique_postfix = datetime.now().isoformat().replace(':', '-').replace('.', '-').lower()
    pkg_title = pkgname  # + '_'

    data_dict = {
                    'name': 'model_configuration_' + unique_postfix,  # this needs to be unique as required by DB
                    'type': 'model-configuration',  # dataset type as defined in custom dataset plugin
                    'title': pkg_title,
                    'owner_org': selected_user_org,
                    'author': tk.c.user or tk.c.author,  # TODO: Need to retrieve user full name
                    'notes': 'This is a dataset consisting of UEB model configuration related resources',
                    'processing_status': 'In queue',
                    'package_build_request_job_id': '',
                    'model_name': 'UEB',
                    'package_availability': uebhelper.StringSettings.app_server_job_status_package_not_available
                 }

    context = {'model': base.model, 'session': base.model.Session, 'user': tk.c.user or tk.c.author, 'save': 'save'}
    try:
        pkg_dict = package_create_action(context, data_dict)
        log.info(source + 'A new dataset was created with name: %s' % data_dict['title']
                 + ' as part of ueb package build request.')
    except Exception as e:
        log.error(source + 'Failed to create a new dataset for ueb_package request for'
                           ' package name: %s \n Exception: %s' % (pkgname, e))

        return None

    pkg_id = pkg_dict['id']

    # add the uploaded ueb request data file as a resource to the above dataset
    try:
        _add_file_to_dataset(context, pkg_dict, request_resource_file)
    except Exception as e:
        log.error(source + ' Failed to update the newly created model-configuration dataset for adding package '
                           'configuration file as a resource.\n Exception: %s' % e)
        tk.get_action('package_delete')(context, {'id': pkg_id})
        log.info(source + ' Deleting the newly created dataset')
        return None

    # for each file id for the user selected files, get the file
    # object and add that to the package/dataset as a link resource
    resource_show_action = tk.get_action('resource_show')

    for file_id in selected_file_ids.values():
        # get the resource that has the id equal to the given resource id
        data_dict = {'id': file_id}
        resource_metadata = resource_show_action(context, data_dict)
        resource_url = resource_metadata.get('url')
        resource_name = resource_metadata.get('name')
        resource_desc = resource_metadata.get('description')
        resource_format = resource_metadata.get('format')
        resource_created_date = resource_metadata.get('_creation_date')
        resource_size = resource_metadata.get('_content_length')

        data_dict = {
                "url": resource_url,
                "name": resource_name,
                "created": resource_created_date,
                "format": resource_format,
                "size": resource_size,
                "description": resource_desc,
                "resource_type": 'file.link',
                "url_type": 'link'
                }
        try:
            pkg_dict = uebhelper.get_package(pkg_id)
            _add_resource_link_to_dataset(context, pkg_dict, data_dict)
        except Exception as e:
            log.error(source + 'Failed to add resource links to the dataset as part of the user selected'
                               ' files for package name: %s \n Exception: %s' % (pkgname, e))
            tk.get_action('package_delete')(context, {'id': pkg_id})
            log.info(source + ' Deleting the newly created dataset')
            return None

    return pkg_id


def _add_file_to_dataset(context, pkg_dict, file_to_add):

    if not 'resources' in pkg_dict:
        pkg_dict['resources'] = []

    file_name = os.path.basename(file_to_add)
    file_name = munge.munge_filename(file_name)
    file_part, file_extension = os.path.splitext(file_to_add)
    # remove the dot from the extension string '.txt' -> 'txt'
    file_extension = file_extension[1:]
    resource = {'url': file_name, 'url_type': 'upload'}
    upload = uploader.ResourceUpload(resource)
    upload.filename = file_name
    upload.upload_file = open(file_to_add, 'r')
    # FIXME The url type setting here to file name is not appropriate. We need to pass the actual resource url
    data_dict = {
                'name': file_name,
                'description': 'UEB configuration settings',
                'format': file_extension,
                'url': file_name,
                'resource_type': 'file.upload',
                'url_type': 'upload'
    }

    pkg_dict['resources'].append(data_dict)

    context['defer_commit'] = True
    context['use_cache'] = False
    # update the package
    package_update_action = tk.get_action('package_update')
    package_update_action(context, pkg_dict)
    context.pop('defer_commit')

    # Get out resource_id resource from model as it will not appear in
    # package_show until after commit
    upload.upload(context['package'].resources[-1].id, uploader.get_max_resource_size())

    base.model.repo.commit()


def _add_resource_link_to_dataset(context, pkg_dict, resource_dict):
    if not 'resources' in pkg_dict:
        pkg_dict['resources'] = []

    pkg_dict['resources'].append(resource_dict)
    context['defer_commit'] = True
    context['use_cache'] = False
    # update the package
    package_update_action = tk.get_action('package_update')
    package_update_action(context, pkg_dict)
    context.pop('defer_commit')
    base.model.repo.commit()


