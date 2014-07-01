import ckan.lib.base as base
import logging
import ckan.plugins as p
from ckan.lib.helpers import json
import ckan.lib.helpers as h
import ckan.lib.uploader as uploader
import httplib
import time
import os
import zipfile as zip
from .. import helpers as uebhelper

tk = p.toolkit
_ = tk._    # translator function

log = logging.getLogger('ckan.logic')


class UEBexecuteController(base.BaseController):
    
    def select_model_package(self):
        source = 'uebpackage.uebexecute.select_model_package():'
        errors = {}
        data = {'selected_pkg_file_id': None}
        error_summary = {}
        form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        tk.c.is_checkbox_checked = False
        tk.c.shape_file_exists = True
        try:
            self._set_context_to_user_input_model_packages()
        except Exception as e:       
            log.error(source + 'CKAN error: %s' % e)
            tk.abort(400, _('CKAN error: %s' % e))
               
        return tk.render('ueb_execute_form.html', extra_vars=form_vars)
        
    def execute(self, pkg_id):

        """
        Executes model input package on app server
        @param pkg_id: id of the model input package to be executed
        @return: ajax_response object
        """
        source = 'uebpackage.uebexecute.execute():'
        # get the model package
        package = uebhelper.get_package(pkg_id)
        ajax_response = uebhelper.AJAXResponse()
        ajax_response.success = False
        ajax_response.message = "Not a valid UEB model package for execution."

        # check that it is a valid model package for execution
        if package['type'] != "model-package":
            return ajax_response.to_json()

        if package.get('package_run_status', None) != 'Not yet submitted':
            ajax_response.message = "This UEB model package has already been executed."
            return ajax_response.to_json()

        # get the package resource zip file
        model_pkg_zip_file = package['resources'][0]

        # get the storage path
        ckan_storage_path = os.path.join(uploader.get_storage_path(), 'resources')

        model_pkg_zip_file_path = os.path.join(ckan_storage_path, model_pkg_zip_file['id'][0:3],
                                               model_pkg_zip_file['id'][3:6], model_pkg_zip_file['id'][6:])

        # send request to app server
        # TODO: read the app server address from config (.ini) file
        service_host_address = uebhelper.StringSettings.app_server_host_address
        service_request_url = uebhelper.StringSettings.app_server_api_run_ueb_url
        connection = httplib.HTTPConnection(service_host_address)
        headers = {'Content-Type': 'application/octet-stream', 'Connection': 'Keep-alive'}
        # for debugging only
        connection.set_debuglevel(1)

        # Let's wait for 0.01 second before calling the webservice
        # Otherwise sometime we get
        # 104 error - Connection Reset by Peer
        # ref: http://stackoverflow.com/questions/383738/104-connection-reset-by-peer-socket-error-or-when-does-closing-a-socket-resu
        time.sleep(0.01)
        with open(model_pkg_zip_file_path, 'r') as ueb_model_pkg_file:
            connection.request('POST', service_request_url, ueb_model_pkg_file, headers)

        service_call_results = connection.getresponse()
        if service_call_results.status == httplib.OK:
            log.info(source + 'Request to execute UEB was successful.')
            service_response_data = service_call_results.read()
            connection.close()
            service_response_dict = json.loads(service_response_data)
            ueb_run_job_id = service_response_dict.get('RunJobID', None)
            response_msg = service_response_dict.get('Message', '')
            if not ueb_run_job_id:
                log.error(source + 'App server failed to process UEB run request.\n' + response_msg)
                ajax_response.message = 'App server failed to process UEB run request.'
                return ajax_response.to_json()
        else:
            connection.close()
            log.error(source + 'App server error: Request to run UEB failed: %s' % service_call_results.reason)
            ajax_response.message = 'App server failed to process UEB run request.'
            return ajax_response.to_json()

        if self._update_ueb_model_pkg_run_job_id(pkg_id, ueb_run_job_id) is None:
            ajax_response.message = 'Failed to update job run ID for the model package.'
            return ajax_response.to_json()

        job_status_processing = uebhelper.StringSettings.app_server_job_status_processing
        if self._update_ueb_model_pkg_run_status(pkg_id, job_status_processing) is None:
            ajax_response.message = 'Failed to update run status for the model package.'
            return ajax_response.to_json()

        base.session.clear()
        tk.c.ueb_run_job_id = ueb_run_job_id
        ajax_response.success = True
        ajax_response.json_data = job_status_processing
        ajax_response.message = "Request to execute UEB was successful."
        return ajax_response.to_json()

    def check_package_run_status(self, pkg_id):

        """
        Calls the app server for a given model package dataset
        to obtain the current status model execution
        @param pkg_id: id of the model package for which model run status to be obtained
        @return: ajax_response object
        """
        source = 'uebpackage.uebexecute.check_package_run_status():'
        # get the model package
        package = uebhelper.get_package(pkg_id)
        ajax_response = uebhelper.AJAXResponse()
        ajax_response.success = False
        ajax_response.message = "Not a valid UEB model package for checking run status."

        # check that it is a valid model package for execution
        if package['type'] != "model-package":
            return ajax_response.to_json()

        if package.get('package_run_status', None) != 'In Queue' and \
                        package.get('package_run_status', None) != 'Processing':

            ajax_response.json_data = package.get('package_run_status', None)
            ajax_response.message = "Status is up-to-date."
            return ajax_response.to_json()

        pkg_run_job_id = package.get('package_run_job_id', None)
        if pkg_run_job_id is None or len(pkg_run_job_id) == 0:
            ajax_response.message = "Looks like this model has not yet submitted for execution."
            return ajax_response.to_json()

        service_host_address = uebhelper.StringSettings.app_server_host_address
        service_request_url = uebhelper.StringSettings.app_server_api_check_ueb_run_status_url
        connection = httplib.HTTPConnection(service_host_address)
        service_request_url = service_request_url + '?uebRunJobID=' + pkg_run_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()

        if service_call_results.status == httplib.OK:
            request_processing_status = service_call_results.read()
            log.info(source + 'UEB model package run status as returned from App '
                              'server for dataset ID: %s and Run Job ID:%s is %s' %
                     (pkg_id, pkg_run_job_id, request_processing_status))
            ajax_response.success = True
            ajax_response.json_data = request_processing_status
            ajax_response.message = "Status check successful."
        else:
            request_processing_status = uebhelper.StringSettings.app_server_job_status_error
            log.error(source + 'HTTP status %d returned from App server when checking '
                               'run status for Run Job ID:%s and model pkg dataset ID:%s' %
                      (service_call_results.status, pkg_run_job_id, pkg_id))

            ajax_response.json_data = request_processing_status
            ajax_response.message = "Status check failed."

        connection.close()
        # update the dataset
        data_dict = {'package_run_status': request_processing_status}
        try:
            uebhelper.update_package(pkg_id, data_dict, backgroundTask=False)
            log.info(source + 'UEB model package dataset run status was updated to %s for '
                          'dataset ID:%s' % (pkg_id, request_processing_status))
        except Exception as e:
            log.error(source + 'Failed to update run status for UEB model package dataset '
                               'with dataset ID:%s\nException:%s' % (pkg_id, e))

        return ajax_response.to_json()

    def retrieve_output_package(self, pkg_id):

        """
        Retrieves the model run output package for given model input package and merges the output package with the
        input package.
        @param pkg_id: id of the model input package
        @return: returns ajax_response object
        """
        source = 'uebpackage.uebexecute.retrieve_output_package():'
        package = uebhelper.get_package(pkg_id)
        ajax_response = uebhelper.AJAXResponse()
        ajax_response.success = False
        ajax_response.message = "Not a valid UEB model package for model run output package retrieval"

        # check that it is a valid model package for execution
        if package['type'] != "model-package":
            return ajax_response.to_json()

        if package.get('package_run_status', None) != 'Success':
            ajax_response.json_data = package.get('package_run_status', None)
            ajax_response.message = "No model run output package is available at this point"
            return ajax_response.to_json()

        pkg_run_job_id = package.get('package_run_job_id', None)
        if pkg_run_job_id is None or len(pkg_run_job_id) == 0:
            ajax_response.message = "Looks like this model has not yet submitted for execution."
            return ajax_response.to_json()

        pkg_type = package.get('package_type', None)
        if pkg_type is None:
            return ajax_response.to_json()

        if pkg_type == u'Complete':
            ajax_response.message = "Looks like the output package has already been retrieved previously."
            return ajax_response.to_json()

        service_host_address = uebhelper.StringSettings.app_server_host_address
        service_request_api_url = uebhelper.StringSettings.app_server_api_get_ueb_run_output
        connection = httplib.HTTPConnection(service_host_address)

        service_request_url = service_request_api_url + '?uebRunJobID=' + pkg_run_job_id
        connection.request('GET', service_request_url)
        service_call_results = connection.getresponse()

        if service_call_results.status == httplib.OK:
            log.info(source + 'UEB model output package was received from App '
                              'server for model pkg dataset ID:%s and Run Job ID:%s' % (pkg_id, pkg_run_job_id))
            success, message = self._merge_ueb_output_pkg_with_input_pkg(service_call_results, pkg_id)
            ajax_response.success = success
            ajax_response.json_data = message
            ajax_response.message = "Model run output package was retrieved and merged with the input package."
        else:
            log.error(source + 'HTTP status %d returned from App server when '
                               'retrieving UEB model output package for '
                               'model pkg dataset ID:%s and Run Job ID:%s' %
                      (service_call_results.status, pkg_id, pkg_run_job_id))

            ajax_response.json_data = uebhelper.StringSettings.app_server_job_status_package_retrieval_failed
            ajax_response.message = "Failed to retrieve model output package."

            # update the dataset
            data_dict = {'package_run_status': ajax_response.json_data}
            try:
                uebhelper.update_package(pkg_id, data_dict, backgroundTask=False)
                log.info(source + 'UEB model package dataset run status was updated to %s for '
                              'dataset ID:%s' % (pkg_id, ajax_response.json_data))
            except Exception as e:
                log.error(source + 'Failed to update run status for UEB model package dataset '
                                   'with dataset ID:%s\nException:%s' % (pkg_id, e))
                pass

        connection.close()
        return ajax_response.to_json()

    # TODO: This needs to be removed since we now have the functionality to execute model package from dataset read page
    def _set_context_to_user_input_model_packages(self):
        # get all datasets of type model-package
        model_pkg_datasets = uebhelper.get_packages_by_dataset_type('model-package')

        # for each resource we need only the id (id be used as the selection value) and the name for display
        file_resources = []

        for dataset in model_pkg_datasets:
            pkg_run_job_id = h.get_pkg_dict_extra(dataset, 'package_run_job_id')
            if pkg_run_job_id is None:
                continue

            # skip dataset if that does not have pkg_model-name = 'UEB'
            pkg_model_name = h.get_pkg_dict_extra(dataset, 'pkg_model_name')
            if pkg_model_name.upper() != 'UEB':
                continue

            # to get the package_type value which is a tag, use the get_package() of my the helper module
            pkg_dict = uebhelper.get_package(dataset['id'])
            pkg_type = pkg_dict['package_type'][0]
            if len(pkg_run_job_id.strip()) != 0:
                continue
            if pkg_type == u'Complete':
                continue

            # check if the dataset is owned by the current user
            dataset_id = dataset['id']
            if not uebhelper.is_user_owns_package(dataset_id, tk.c.user) and \
                    not uebhelper.is_user_owns_package(dataset_id, 'default'):
                continue

            # get model package zip file resource from the dataset and we assume the dataset has only one resource
            model_pkg_resource = dataset['resources'][0]
            dataset_title = dataset['title']
            max_len = 50
            if len(dataset_title) > max_len:
                dataset_title = dataset_title[:max_len] + '...'

            dataset_title = ' (' + dataset_title + ')'
            resource = {}
            resource['id'] = model_pkg_resource['id']
            resource['url'] = model_pkg_resource['url']
            resource['name'] = model_pkg_resource['name'] + dataset_title
            resource['description'] = model_pkg_resource['description']
            file_resources.append(resource)

        tk.c.ueb_input_model_packages = file_resources

    def _update_ueb_model_pkg_run_job_id(self, ueb_model_pkg_dataset_id, run_job_id):

        """
        Updates a ueb model package dataset's package_run_job_id custom field

        ueb_model_pkg_dataset_id: id of the model package dataset to be updated
        param run_job_id: ueb run job id returned from app server responsible for running ueb
        @rtype: updated model package dataset dictionary if successful otherwise None

        """
        data_dict = {'package_run_job_id': run_job_id}
        update_msg = 'system auto updated model package dataset'
        background_task = False
        updated_package = None
        try:
            updated_package = uebhelper.update_package(ueb_model_pkg_dataset_id, data_dict, update_msg, background_task)
            log.info('Model package dataset was updated as a result of '
                              'package submission for execution for dataset:%s' % updated_package['name'])
        except Exception as e:
            log.error('Failed to update model package dataset after '
                               'submitting package for execution for dataset ID:%s \n'
                               'Exception: %s' % (ueb_model_pkg_dataset_id, e))
            pass

        return updated_package

    def _update_ueb_model_pkg_run_status(self, ueb_model_pkg_dataset_id, status):

        """
        Updates a ueb model package dataset's package_run_job_id custom field

        ueb_model_pkg_dataset_id: id of the model package dataset to be updated
        param run_job_id: ueb run job id returned from app server responsible for running ueb
        @rtype: updated model package dataset dictionary if successful otherwise None

        """
        data_dict = {'package_run_status': status}
        update_msg = 'system auto updated model package dataset'
        background_task = False
        updated_package = None
        try:
            updated_package = uebhelper.update_package(ueb_model_pkg_dataset_id, data_dict, update_msg, background_task)
            log.info('Model package dataset was updated as a result of '
                        'receiving model run status update from app server for dataset:%s' % updated_package['name'])
        except Exception as e:
            log.error('Failed to update model package dataset after '
                        'receiving model run status update from app server for dataset ID:%s \n'
                               'Exception: %s' % (ueb_model_pkg_dataset_id, e))
            pass

        return updated_package

    def _merge_ueb_output_pkg_with_input_pkg(self, service_call_results, model_pkg_dataset_id):

        """
        Merges the model run output data with the model input package
        @param service_call_results: http service response object returned from the app server
        @param model_pkg_dataset_id: id of the input model package
        @return: success (True or False) and message ( a string value) representing the status to be set for model
        package run status attribute
        """
        source = 'uebpackage.tasks._merge_ueb_output_pkg_with_input_pkg():'

        # save the output model pkg to temp directory
        ckan_default_dir = uebhelper.StringSettings.ckan_user_session_temp_dir
        # create a directory for saving the file
        # this will be a dir in the form of: /tmp/ckan/{random_id}
        random_id = base.model.types.make_uuid()
        destination_dir = os.path.join(ckan_default_dir, random_id)
        os.makedirs(destination_dir)
        ueb_output_pkg_filename = uebhelper.StringSettings.ueb_output_model_package_default_filename
        ueb_output_pkg_file = os.path.join(destination_dir, ueb_output_pkg_filename)

        bytes_to_read = 16 * 1024
        success = False
        message = uebhelper.StringSettings.app_server_job_status_package_retrieval_failed
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

            return success, message

        log.info(source + 'ueb model output package zip file was saved to temporary location '
                          'for model package dataset ID: %s' % model_pkg_dataset_id)

        # access the input model pkg zip file
        model_pkg_dataset = uebhelper.get_package(model_pkg_dataset_id)
        # get the package resource zip file
        model_pkg_zip_file = model_pkg_dataset['resources'][0]

        # get the storage path of the pkg zip file
        ckan_storage_path = os.path.join(uploader.get_storage_path(), 'resources')

        model_pkg_zip_file_path = os.path.join(ckan_storage_path, model_pkg_zip_file['id'][0:3],
                                               model_pkg_zip_file['id'][3:6], model_pkg_zip_file['id'][6:])

        '''
        open the original input zip file in the append mode and then
        read the output pkg zip file and append it to the original zip file
        '''
        is_merge_successful = False
        try:
            with zip.ZipFile(model_pkg_zip_file_path, 'a') as orig_file_obj:
                zip_file_to_merge = zip.ZipFile(ueb_output_pkg_file, 'r')
                for fname in zip_file_to_merge.namelist():
                    orig_file_obj.writestr(fname, zip_file_to_merge.open(fname).read())

            is_merge_successful = True
        except Exception as e:
            log.error(source + 'Failed to merge output model pkg zip file with the input model pkg zip file '
                               'for model package dataset ID: %s \n '
                               'Exception: %s' % (model_pkg_dataset_id, e))

        # update the model package dataset package_type to complete
        if is_merge_successful:
            data_dict = {'package_run_status': uebhelper.StringSettings.app_server_job_status_package_retrieval_success, 'package_type': u'Complete'}
            success = True
            message = uebhelper.StringSettings.app_server_job_status_package_retrieval_success
        else:
            data_dict = {'package_run_status': uebhelper.StringSettings.app_server_job_status_package_retrieval_failed}

        update_msg = 'system auto updated ueb package dataset'
        background_task = False
        try:
            updated_package = uebhelper.update_package(model_pkg_dataset_id, data_dict, update_msg, background_task)
            log.info(source + 'UEB model package dataset was updated as a result of '
                              'receiving model output package for dataset:%s' % updated_package['name'])
        except Exception as e:
            log.error(source + 'Failed to update UEB model package dataset after '
                               'receiving model input package for dataset ID:%s \n'
                               'Exception: %s' % (model_pkg_dataset_id, e))

        return success, message