#TODO: delete this py file as we no more using background tasks
#from ckan.lib.celery_app import celery
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
from ckan.controllers import storage
import ckan.lib.munge as munge
import ckan.lib.uploader as uploader
import httplib
import os
from datetime import datetime
import helpers as uebhelper
import logging
import zipfile as zip

_ = tk._  # translator function

log = logging.getLogger('ckan.logic')

service_host_address = uebhelper.StringSettings.app_server_host_address  # 'thredds-ci-water.bluezone.usu.edu'

#@celery.task
def add(x, y):
    return x + y

#@celery.task
def check_ueb_request_process_status():
    source = 'uebpackage.tasks.check_ueb_request_process_status():'
    global service_host_address

    service_request_api_url = uebhelper.StringSettings.app_server_api_check_ueb_package_build_status
    connection = httplib.HTTPConnection(service_host_address)
    job_status_processing = uebhelper.StringSettings.app_server_job_status_processing

    model_config_datasets_with_status_processing = _get_model_configuration_datasets_by_processing_status(
        job_status_processing)

    job_status_in_queue = uebhelper.StringSettings.app_server_job_status_in_queue

    model_config_datasets_with_status_in_queue = _get_model_configuration_datasets_by_processing_status(
        job_status_in_queue)

    # merge the 2 lists
    model_config_datasets_with_status_processing_or_in_queue = model_config_datasets_with_status_processing + \
                                                               model_config_datasets_with_status_in_queue

    if len(model_config_datasets_with_status_processing_or_in_queue) == 0:
        log.info(source + "No UEB model configuration dataset has a status of %s or %s at this time"
                 % (job_status_processing, job_status_in_queue))
    else:
        log.info(source + "Number of UEB model configuration datasets build status of %s or %s at this time is:%s"
                 % (job_status_processing, job_status_in_queue,
                    len(model_config_datasets_with_status_processing_or_in_queue)))

    for dataset in model_config_datasets_with_status_processing_or_in_queue:
        #pkg_process_job_id = h.get_pkg_dict_extra(dataset, 'package_build_request_job_id')

        # in CKAN 2.2 additional metatadata elements added to the dataset of specific type
        # seems not part of the 'extra' key of the dataset dict. These additional metadata elements
        # are now part of the dataset main dictionary
        pkg_process_job_id = dataset.get('package_build_request_job_id', None)
        #pkg_current_processing_status = h.get_pkg_dict_extra(dataset, 'processing_status')
        pkg_current_processing_status = dataset.get('processing_status', None)

        if pkg_process_job_id and pkg_current_processing_status:
            dataset_id = dataset['id']
            service_request_url = service_request_api_url + '?packageID=' + pkg_process_job_id
            connection.request('GET', service_request_url)
            service_call_results = connection.getresponse()

            if service_call_results.status == httplib.OK:
                request_processing_status = service_call_results.read()
                log.info(source + 'UEB model package build status as returned from App server '
                                  'for PackageJobID:%s is %s' % (pkg_process_job_id, request_processing_status))
            else:
                request_processing_status = uebhelper.StringSettings.app_server_job_status_error
                log.error(source + 'HTTP status %d returned from App server when checking '
                                   'status for PackageJobID:%s' % (service_call_results.status, pkg_process_job_id))

            connection.close()

            # update the dataset if the status has changed
            if pkg_current_processing_status != request_processing_status:
                data_dict = {'processing_status': request_processing_status}
                uebhelper.update_package(dataset_id, data_dict, backgroundTask=True)
        else:
            log.error(source + "Either the metadata element 'package_build_request_job_id' "
                               "or the 'processing_status' was not found "
                               "for dataset ID:%s" % dataset['id'])


def check_ueb_run_status():
    source = 'uebpackage.tasks.check_ueb_run_status():'
    global service_host_address

    service_request_api_url = uebhelper.StringSettings.app_server_api_check_ueb_run_status_url
    connection = httplib.HTTPConnection(service_host_address)
    job_status_processing = uebhelper.StringSettings.app_server_job_status_processing
    job_status_in_queue = uebhelper.StringSettings.app_server_job_status_in_queue

    model_pkg_datasets_with_run_status_processing = _get_model_pkg_datasets_by_run_status(job_status_processing)
    model_pkg_datasets_with_run_status_in_queue = _get_model_pkg_datasets_by_run_status(job_status_in_queue)

    model_pkg_datasets_need_run_status_update = model_pkg_datasets_with_run_status_processing + \
                                                model_pkg_datasets_with_run_status_in_queue

    if len(model_pkg_datasets_need_run_status_update) == 0:
        log.info(source + "No UEB model package dataset has a run status of %s at this time" % job_status_processing)
    else:
        log.info(source + "Number of UEB model package datatsets with run status of %s or %s at this time is:%s"
                 % (job_status_processing, job_status_in_queue, len(model_pkg_datasets_need_run_status_update)))

    for dataset in model_pkg_datasets_need_run_status_update:
        pkg_run_job_id = h.get_pkg_dict_extra(dataset, 'package_run_job_id')
        if pkg_run_job_id is None:
            continue

        dataset_id = dataset['id']
        service_request_url = service_request_api_url + '?uebRunJobID=' + pkg_run_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()

        if service_call_results.status == httplib.OK:
            request_processing_status = service_call_results.read()
            log.info(source + 'UEB model package run status as returned from App '
                              'server for dataset ID: %s and Run Job ID:%s is %s' %
                     (dataset_id, pkg_run_job_id, request_processing_status))
        else:
            request_processing_status = uebhelper.StringSettings.app_server_job_status_error
            log.error(source + 'HTTP status %d returned from App server when checking '
                               'run status for Run Job ID:%s and model pkg dataset ID:%s' %
                      (service_call_results.status, pkg_run_job_id, dataset_id))

        connection.close()
        # update the dataset
        data_dict = {'package_run_status': request_processing_status}
        try:
            uebhelper.update_package(dataset_id, data_dict, backgroundTask=True)
            log.info(source + 'UEB model package dataset run status was updated to %s for '
                          'dataset ID:%s' % (dataset_id, request_processing_status))
        except Exception as e:
            log.error(source + 'Failed to update run status for UEB model package dataset '
                               'with dataset ID:%s\nException:%s' % (dataset_id, e))


#@celery.task
def retrieve_ueb_packages():
    source = 'uebpackage.tasks.retrieve_ueb_packages():'
    global service_host_address
    service_request_api_url = uebhelper.StringSettings.app_server_api_get_ueb_package_url
    connection = httplib.HTTPConnection(service_host_address)
    job_status_complete = uebhelper.StringSettings.app_server_job_status_success
    model_config_datasets_with_status_complete = _get_model_configuration_datasets_by_processing_status(
        job_status_complete)

    if len(model_config_datasets_with_status_complete) == 0:
        log.info(source + "No UEB model configuration dataset has a status of %s at this time" % job_status_complete)
    else:
        log.info(source + "Number of UEB model configuration datasets with build status of %s at this time is:%s"
                 % (job_status_complete, len(model_config_datasets_with_status_complete)))

    for dataset in model_config_datasets_with_status_complete:
        pkg_availability_status = h.get_pkg_dict_extra(dataset, 'package_availability')
        if pkg_availability_status == uebhelper.StringSettings.app_server_job_status_package_available:
            continue

        pkg_process_job_id = h.get_pkg_dict_extra(dataset, 'package_build_request_job_id')
        dataset_id = dataset['id']
        package_availability_status = h.get_pkg_dict_extra(dataset, 'package_availability')

        # if package is already available or error has been logged for package retrieval then skip this dataset
        if package_availability_status == uebhelper.StringSettings.app_server_job_status_package_available or \
                package_availability_status == uebhelper.StringSettings.app_server_job_status_error:
            continue

        service_request_url = service_request_api_url + '?packageID=' + pkg_process_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()

        if service_call_results.status == httplib.OK:
            log.info(source + 'UEB model package was received from App server for PackageJobID:%s' % pkg_process_job_id)
            try:
                _save_ueb_package_as_dataset(service_call_results, dataset_id)
                pkg_availability_status = uebhelper.StringSettings.app_server_job_status_package_available
            except Exception as e:
                log.error(source + 'Failed to save ueb model package as a new dataset '
                                   'for model configuration dataset ID:%s\nException:%s' % (dataset_id, e))
                pkg_availability_status = uebhelper.StringSettings.app_server_job_status_error
        else:
            log.error(source + 'HTTP status %d returned from App server when retrieving '
                               'UEB model package for PackageJobID:'
                               '%s' % (service_call_results.status, pkg_process_job_id))
            pkg_availability_status = uebhelper.StringSettings.app_server_job_status_error

        connection.close()

        # update the resource processing status
        # update the related dataset
        data_dict = {'package_availability': pkg_availability_status}
        update_msg = 'system auto updated ueb package dataset'
        background_task = True
        try:
            updated_package = uebhelper.update_package(dataset_id, data_dict, update_msg, background_task)
            log.info(source + 'UEB model configuration dataset was updated as a result of '
                              'receiving model input package for dataset:%s' % updated_package['name'])
        except Exception as e:
            log.error(source + 'Failed to update UEB model configuration dataset after '
                               'receiving model input package for dataset ID:%s \n'
                               'Exception: %s' % (dataset_id, e))
            pass

    return


def retrieve_ueb_run_output_packages():
    source = 'uebpackage.tasks.retrieve_ueb_run_output_packages():'
    global service_host_address
    #service_request_api_url = '/api/UEBModelRunOutput'
    service_request_api_url = uebhelper.StringSettings.app_server_api_get_ueb_run_output
    connection = httplib.HTTPConnection(service_host_address)

    # get all datasets of type model-package
    model_pkg_datasets = uebhelper.get_packages_by_dataset_type('model-package')
    for dataset in model_pkg_datasets:
        pkg_run_job_id = h.get_pkg_dict_extra(dataset, 'package_run_job_id')
        if pkg_run_job_id is None:
            continue

        # to get the package_type value which is a tag, use the get_package() of my the helper module
        pkg_dict = uebhelper.get_package(dataset['id'])
        # TODO: Before using pkg_dict check that it is not None
        pkg_type = pkg_dict['package_type'][0]
        if len(pkg_run_job_id) == 0:
            continue
        if pkg_type == u'Complete':
            continue

        pkg_run_status = h.get_pkg_dict_extra(dataset, 'package_run_status')
        if pkg_run_status != uebhelper.StringSettings.app_server_job_status_success:
            continue

        dataset_id = dataset['id']
        service_request_url = service_request_api_url + '?uebRunJobID=' + pkg_run_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()

        if service_call_results.status == httplib.OK:
            log.info(source + 'UEB model output package was received from App '
                              'server for model pkg dataset ID:%s and Run Job ID:%s' % (dataset_id, pkg_run_job_id))
            _merge_ueb_output_pkg_with_input_pkg(service_call_results, dataset_id)
        else:
            log.error(source + 'HTTP status %d returned from App server when '
                               'retrieving UEB model output package for '
                               'model pkg dataset ID:%s and Run Job ID:%s' %
                      (service_call_results.status, dataset_id, pkg_run_job_id))

            ueb_run_status = 'Failed to retrieve output package'

            # update the dataset
            data_dict = {'package_run_status': ueb_run_status}
            try:
                uebhelper.update_package(dataset_id, data_dict, backgroundTask=True)
                log.info(source + 'UEB model package dataset run status was updated to %s for '
                              'dataset ID:%s' % (dataset_id, ueb_run_status))
            except Exception as e:
                log.error(source + 'Failed to update run status for UEB model package dataset '
                                   'with dataset ID:%s\nException:%s' % (dataset_id, e))

        connection.close()

    return


def _save_ueb_package_as_dataset(service_call_results, model_config_dataset_id):
    source = 'uebpackage.tasks._save_ueb_package_as_dataset():'
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

    # upload the file to CKAN file store
    # resource_metadata = _upload_file(model_pkg_file)
    # if resource_metadata:
    #     log.info(source + 'UEB model package zip file was uploaded for model configuration dataset ID:%s' % model_config_dataset_id)
    # else:
    #     log.error(source + 'Failed to upload UEB model package zip file '
    #                        'for model configuration dataset ID: %s' % model_config_dataset_id)
    #     return
    #
    # # retrieve some of the file meta data
    # resource_url = resource_metadata.get('_label')  # this will return datetime stamp/filename
    #
    # resource_url = '/storage/f/' + resource_url
    # if resource_url.startswith('/'):
    #     resource_url = base.config.get('ckan.site_url', '').rstrip('/') + resource_url
    # else:
    #     resource_url = base.config.get('ckan.site_url', '') + resource_url
    #
    # resource_created_date = resource_metadata.get('_creation_date')
    # resource_name = resource_metadata.get('filename_original')
    # resource_size = resource_metadata.get('_content_length')
    #
    # # add the uploaded ueb model pkg data file as a resource to the dataset
    # resource_create_action = tk.get_action('resource_create')
    # context = {'model': base.model, 'session': base.model.Session, 'save': 'save'}
    # user = uebhelper.get_site_user()
    # context['user'] = user.get('name')
    # context['ignore_auth'] = True
    # context['validate'] = False

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
        uebhelper.register_translator()     # this is needed since we are creating a package in a background operation
        pkg_dict = package_create_action(context, data_dict)
        log.info(source + 'A new dataset was created for UEB input model package with name: %s' % data_dict['title'])
    except Exception as e:
        log.error(source + 'Failed to create a new dataset for ueb input model package for'
                           ' the related model configuration dataset title: %s \n Exception: %s' % (pkg_title, e))
        raise e

    pkg_id = pkg_dict['id']

    if not 'resources' in pkg_dict:
        pkg_dict['resources'] = []

    file_name = munge.munge_filename(model_pkg_filename)
    resource = {'url': file_name, 'url_type': 'upload'}
    upload = uploader.ResourceUpload(resource)
    upload.filename = file_name
    upload.upload_file = open(model_pkg_file, 'r')
    data_dict = {'format': 'zip', 'name': file_name, 'url': file_name, 'url_type': 'upload'}
    pkg_dict['resources'].append(data_dict)

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

    # link this newly created model package dataset to the model configuration dataset
    package_relationship_create_action = tk.get_action('package_relationship_create')
    data_dict = {'subject': pkg_id, 'object': model_config_dataset_id, 'type': 'links_to'}
    package_relationship_create_action(context, data_dict)

    # Get out resource_id resource from model as it will not appear in
    # package_show until after commit
    upload.upload(context['package'].resources[-1].id, uploader.get_max_resource_size())
    base.model.repo.commit()

    # update the related model configuration dataset to show that the package is available

    data_dict = {'package_availability': 'Available'}
    update_msg = 'system auto updated ueb package dataset'
    background_task = True
    try:
        updated_package = uebhelper.update_package(model_config_dataset_id, data_dict, update_msg, background_task)
        log.info(source + 'UEB model configuration dataset was updated as a result of '
                          'receiving model input package for dataset:%s' % updated_package['name'])
    except Exception as e:
        log.error(source + 'Failed to update UEB model configuration dataset after '
                           'receiving model input package for dataset ID:%s \n'
                           'Exception: %s' % (model_config_dataset_id, e))
        raise e


# TODO: Once the above method tested to work, the following method needs to be deleted
def _save_ueb_package_as_dataset_obsolete(service_call_results, model_config_dataset_id):
    source = 'uebpackage.tasks._save_ueb_package_as_dataset():'
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

    # upload the file to CKAN file store
    resource_metadata = _upload_file(model_pkg_file)
    if resource_metadata:
        log.info(source + 'UEB model package zip file was uploaded for model configuration dataset ID:%s' % model_config_dataset_id)
    else:
        log.error(source + 'Failed to upload UEB model package zip file '
                           'for model configuration dataset ID: %s' % model_config_dataset_id)
        return

    # retrieve some of the file meta data
    resource_url = resource_metadata.get('_label')  # this will return datetime stamp/filename

    resource_url = '/storage/f/' + resource_url
    if resource_url.startswith('/'):
        resource_url = base.config.get('ckan.site_url', '').rstrip('/') + resource_url
    else:
        resource_url = base.config.get('ckan.site_url', '') + resource_url

    resource_created_date = resource_metadata.get('_creation_date')
    resource_name = resource_metadata.get('filename_original')
    resource_size = resource_metadata.get('_content_length')

    # add the uploaded ueb model pkg data file as a resource to the dataset
    resource_create_action = tk.get_action('resource_create')
    context = {'model': base.model, 'session': base.model.Session, 'save': 'save'}
    user = uebhelper.get_site_user()
    context['user'] = user.get('name')
    context['ignore_auth'] = True
    context['validate'] = False

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
        uebhelper.register_translator()     # this is needed since we are creating a package in a background operation
        pkg_dict = package_create_action(context, data_dict)
        log.info(source + 'A new dataset was created for UEB input model package with name: %s' % data_dict['title'])
    except Exception as e:
        log.error(source + 'Failed to create a new dataset for ueb input model package for'
                           ' the related model configuration dataset title: %s \n Exception: %s' % (pkg_title, e))
        return

    pkg_id = pkg_dict['id']
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
                "description": 'UEB model package'
                }

    is_resource_add_success = False
    try:
        resource_create_action(context, data_dict)
        is_resource_add_success = True
        log.info(source + 'UEB model package was added as a resource to the '
                          'newly created model package dataset with ID:%s' % pkg_id)
    except Exception as e:
        log.error(source + 'Failed to add UEB model package as a resource to '
                           'the newly created model package dataset with ID:%s \nException: %s' % (pkg_id, e))
        pass

    # link this newly created model package dataset to the model configuration dataset
    package_relationship_create_action = tk.get_action('package_relationship_create')
    data_dict = {'subject': pkg_id, 'object': model_config_dataset_id, 'type': 'links_to'}
    package_relationship_create_action(context, data_dict)

    # update the related model configuration dataset to show that the package is available
    if is_resource_add_success:
        # update the related dataset
        data_dict = {'package_availability': 'Available'}
        update_msg = 'system auto updated ueb package dataset'
        background_task = True
        try:
            updated_package = uebhelper.update_package(model_config_dataset_id, data_dict, update_msg, background_task)
            log.info(source + 'UEB model configuration dataset was updated as a result of '
                              'receiving model input package for dataset:%s' % updated_package['name'])
        except Exception as e:
            log.error(source + 'Failed to update UEB model configuration dataset after '
                               'receiving model input package for dataset ID:%s \n'
                               'Exception: %s' % (model_config_dataset_id, e))
            pass
    return


def _merge_ueb_output_pkg_with_input_pkg(service_call_results, model_pkg_dataset_id):
    source = 'uebpackage.tasks._merge_ueb_output_pkg_with_input_pkg():'

    # save the output model pkg to temp directory
    #ckan_default_dir = '/tmp/ckan'
    ckan_default_dir = uebhelper.StringSettings.ckan_user_session_temp_dir
    # create a directory for saving the file
    # this will be a dir in the form of: /tmp/ckan/{random_id}
    random_id = base.model.types.make_uuid()
    destination_dir = os.path.join(ckan_default_dir, random_id)
    os.makedirs(destination_dir)
    ueb_output_pkg_filename = uebhelper.StringSettings.ueb_output_model_package_default_filename
    ueb_output_pkg_file = os.path.join(destination_dir, ueb_output_pkg_filename)

    bytes_to_read = 16 * 1024

    try:
        with open(ueb_output_pkg_file, 'wb') as file_obj:
            while True:
                data = service_call_results.read(bytes_to_read)
                if not data:
                    break
                file_obj.write(data)
    except Exception as e:
        log.error(source + 'Failed to save ueb model output package zip file to '
                           'temporary location for model package dataset ID: %s \n '
                           'Exception: %s' % (model_pkg_dataset_id, e))
        pass
        return  # no need to show error to the user as this a background operation

    log.info(source + 'ueb model output package zip file was saved to temporary location '
                      'for model package dataset ID: %s' % model_pkg_dataset_id)

    # access the input model pkg zip file
    model_pkg_dataset = uebhelper.get_package(model_pkg_dataset_id)
    # TODO: Before using model_pk_dataset check that it is not None
    model_pkg_resource_zip_file = model_pkg_dataset['resources'][0]

    # replace the  '%3A' in the file url with ':' to get the correct folder name in the file system
    pkg_zip_file_url = model_pkg_resource_zip_file['url']
    pkg_zip_file_url = pkg_zip_file_url.replace('%3A', ':')
    sting_to_search_in_file_url = 'storage/f/'
    search_string_index = pkg_zip_file_url.find(sting_to_search_in_file_url)
    file_path_start_index = search_string_index + len(sting_to_search_in_file_url)
    original_zip_file_path = pkg_zip_file_url[file_path_start_index:]
    original_zip_file_path = os.path.join('/', 'var', 'lib', 'ckan', 'default', 'pairtree_root', 'de', 'fa', 'ul', 't', 'obj', original_zip_file_path)

    '''
    open the original input zip file in the append mode and then
    read the output pkg zip file and append it to the original zip file
    '''
    is_merge_successful = False
    try:
        with zip.ZipFile(original_zip_file_path, 'a') as orig_file_obj:
            zip_file_to_merge = zip.ZipFile(ueb_output_pkg_file, 'r')
            for fname in zip_file_to_merge.namelist():
                orig_file_obj.writestr(fname, zip_file_to_merge.open(fname).read())

        is_merge_successful = True
    except Exception as e:
        log.error(source + 'Failed to merge output model pkg zip file with the input model pkg zip file '
                           'for model package dataset ID: %s \n '
                           'Exception: %s' % (model_pkg_dataset_id, e))
        pass

    # update the model package dataset package_type to complete
    if is_merge_successful:
        data_dict = {'package_run_status': 'Output package available', 'package_type': u'Complete'}
    else:
        data_dict = {'package_run_status': 'Success'}   # TODO: set to 'Success' for testing. Finally needs to be set "Merge failed"

    update_msg = 'system auto updated ueb package dataset'
    background_task = True
    try:
        updated_package = uebhelper.update_package(model_pkg_dataset_id, data_dict, update_msg, background_task)
        log.info(source + 'UEB model package dataset was updated as a result of '
                          'receiving model output package for dataset:%s' % updated_package['name'])
    except Exception as e:
        log.error(source + 'Failed to update UEB model package dataset after '
                           'receiving model input package for dataset ID:%s \n'
                           'Exception: %s' % (model_pkg_dataset_id, e))
        pass


def _upload_file(file_path):
    """
    uploads a file to ckan filestore and returns file metadata
    related to its existance in ckan
    param file_path: name of the file with its current location (path)
    """
    source = 'uebpackage.tasks._upload_file():'
    # this code has been implemented based on the code for the upload_handle() method
    # in storage.py    
    bucket_id = base.config.get('ckan.storage.bucket', 'default')
    ts = datetime.now().isoformat().split(".")[0]  # '2010-07-08T19:56:47'    
    file_name = os.path.basename(file_path).replace(' ', '-') # ueb request.txt -> ueb-request.txt
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


def _get_model_configuration_datasets_by_processing_status(status):
    matching_datasets = uebhelper.get_packages_by_dataset_type('model-configuration')
    #filtered_datasets = []
    filtered_datasets = [dataset for dataset in matching_datasets if 'processing_status' in dataset and
                                                                     dataset['processing_status'] == status]
    # for dataset in matching_datasets:
    #     if 'extras' in dataset:
    #         extras = dataset['extras']
    #         for extra in extras:
    #             if extra['key'] == 'processing_status' and extra['value'] == status:
    #                 filtered_datasets.append(dataset)
    #                 break
    # for dataset in matching_datasets_with_status:
    #     uploaded_resources = [res for res in dataset['resources'] if res['url_type'] == 'upload']
    #     if len(uploaded_resources) == 0:
    #         filtered_datasets.append(dataset)

    return filtered_datasets


def _get_model_pkg_datasets_by_run_status(status):
    matching_datasets = uebhelper.get_packages_by_dataset_type('model-package')
    filtered_datasets = []
    for dataset in matching_datasets:
        extras = dataset['extras']
        for extra in extras:
            if extra['key'] == 'package_run_status' and extra['value'] == status:
                filtered_datasets.append(dataset)
                break

    return filtered_datasets


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
        # filter out any deleted resources
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
        # filter out any deleted resources
        active_resource = uebhelper.get_resource(file_resource['id'])
        if not active_resource:
            continue
        ueb_pkg_active_requests.append(active_resource)

    return ueb_pkg_active_requests
