import ckan.lib.base as base
import logging
import ckan.plugins as p
from ckan.lib.helpers import json
import ckan.lib.helpers as h
import httplib
import time
import os
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
        
    def execute(self):
        # TODO: Instead of aborting in case of error, pass an error message to html page
        # retrieve the url of the selected model pkg
        # open the model pkg as a readable file object and pass the file object as the body of the
        # web service request
        # send the request to app server and wait to get the job ID
        # Update the status of the model pkg to record this JobID        
        source = 'uebpackage.uebexecute.execute():'
        resource_show_action = tk.get_action('resource_show')
        ueb_model_pkg_resource_id = tk.request.params['uebpkgfile_id']
        context = {'model': base.model, 'session': base.model.Session,
                   'user': tk.c.user or tk.c.author}

        data_dict = {'id': ueb_model_pkg_resource_id}
        try:
            matching_file_resource = resource_show_action(context, data_dict)
            file_url = matching_file_resource.get('url')

            # replace the  '%3A' in the file url with ':' to get the correct folder name in the file system
            file_url = file_url.replace('%3A', ':')
            sting_to_search_in_file_url = 'storage/f/'
            search_string_index = file_url.find(sting_to_search_in_file_url)
            file_path_start_index = search_string_index + len(sting_to_search_in_file_url)
            file_path = file_url[file_path_start_index:]
                    
            # get a file object in read mode pointing to the matching file in file store
            source_file_obj = uebhelper.retrieve_file_object_from_file_store(file_path)

        except Exception as e:       
            log.error(source + 'CKAN error: %s' % e)
            tk.abort(400, _('CKAN error: %s' % e))

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
        with open(source_file_obj.name, 'r') as ueb_model_pkg_file:
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
                log.error(source + 'App server failed to process UEB run request.')
                tk.abort(400, _('App server failed to process UEB run request: %s' % response_msg))
        else:
            connection.close()
            log.error(source + 'App server error: Request to run UEB failed: %s' % service_call_results.reason)
            tk.abort(400, _('App server error: Request to run UEB failed: %s' % service_call_results.reason))

        # get the dataset of the model pkg zip file and update it
        model_pkg_dataset_of_pkg_resource = uebhelper.get_package_for_resource(ueb_model_pkg_resource_id)
        if self._update_ueb_model_pkg_run_job_id(model_pkg_dataset_of_pkg_resource['id'], ueb_run_job_id) is None:
            tk.abort(400, _('CKAN error: Failed to update UEB model package dataset job ID.'))

        job_status_processing = uebhelper.StringSettings.app_server_job_status_processing
        if self._update_ueb_model_pkg_run_status(model_pkg_dataset_of_pkg_resource['id'],
                                                 job_status_processing) is None:
            tk.abort(400, _('CKAN error: Failed to update UEB model package dataset run status.'))

        base.session.clear()
        tk.c.ueb_run_job_id = ueb_run_job_id
        return tk.render('ueb_run_request_submission.html')

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