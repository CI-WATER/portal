import ckan.lib.base as base
import logging
import ckan.plugins as p
from ckan.lib.helpers import json
import httplib
import time
from .. import helpers as uebhelper

tk = p.toolkit
_ = tk._    # translator function

log = logging.getLogger('ckan.logic')


class UEBexecuteController(base.BaseController):
    
    def select_model_package(self):
        source = 'uebpackage.uebexecute.select_model_package():'
        errors = {}
        data = {}
        data['selected_pkg_file_id'] = None
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
        ueb_model_pkg_CKAN_id = tk.request.params['uebpkgfile_id']  
        context = {'model': base.model, 'session': base.model.Session,
                   'user': tk.c.user or tk.c.author}

        data_dict = {'id': ueb_model_pkg_CKAN_id}
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
        #service_host_address = 'thredds-ci-water.bluezone.usu.edu'
        service_host_address = uebhelper.StringSettings.app_server_host_address
        #service_request_url = '/api/RunUEB'
        service_request_url = uebhelper.StringSettings.app_server_api_run_ueb_url
        connection = httplib.HTTPConnection(service_host_address)
        headers = {'Content-Type': 'application/octet-stream', 'Connection': 'Keep-alive'}  # 'multipart/form-data'
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
        
        if self._update_ueb_model_pkg_run_job_id(ueb_model_pkg_CKAN_id, ueb_run_job_id) is None:
            tk.abort(400, _('CKAN error: Failed to update UEB input model package resource job ID.'))

        job_status_processing = uebhelper.StringSettings.app_server_job_status_processing
        if self._update_ueb_model_pkg_run_status(ueb_model_pkg_CKAN_id, job_status_processing) is None:
            tk.abort(400, _('CKAN error: Failed to update UEB input model package resource status.'))
        else:
            base.session.clear()
            tk.c.ueb_run_job_id = ueb_run_job_id
            return tk.render('ueb_run_request_submission.html')

    def _set_context_to_user_input_model_packages(self):
        # note: resource_search returns a list of matching resources
        # that can include any deleted resources
        resource_search_action = tk.get_action('resource_search')
        context = {'model': base.model, 'session': base.model.Session,
                   'user': tk.c.user or tk.c.author, 'for_view': True}
        
        # get the resource that has the format field set to zip
        # and the ResourceType is 'UEB Input Package'
        data_dict = {'query': ['format:zip', 'ResourceType:UEB Input Package']}
        shape_file_resources = resource_search_action(context, data_dict)['results']
        
        # for each resource we need only the id (id be used as the selection value) and the name for display
        file_resources = []
        for file_resource in shape_file_resources:
            resource = {}
            # filter out any deleted resources
            active_resource = uebhelper.get_resource(file_resource['id'])
            if not active_resource:
                continue            
            
            #check if this input model pkg resource has a value for the 
            #extra metadata field- UEBRunStatus meaning this package has been
            #already used for running UEB. In that case skip this resource
            ueb_run_status = file_resource.get('UEBRunStatus', None)
            if ueb_run_status:
                continue
            
            # get the matching resource object and then get the id of the related package
            resource_obj = base.model.Resource.get(file_resource['id'])
            related_pkg_obj = resource_obj.resource_group.package           
            pkg_title = related_pkg_obj.title
            # remove the datestamp part of the package title which starts with an underscore
            underscore_index = pkg_title.find('_')
            if underscore_index != -1:
                pkg_title = pkg_title[:underscore_index]

            max_len = 50
            if len(pkg_title) > max_len:
                pkg_title = pkg_title[:max_len] + '...'

            pkg_title = ' (' + pkg_title + ')'
                
            resource['id'] = file_resource['id']
            resource['url'] = file_resource['url']
            resource['name'] = file_resource['name'] + pkg_title
            resource['description'] = file_resource['description'] 
            file_resources.append(resource) 
                       
        tk.c.ueb_input_model_packages = file_resources  
    
    def _update_ueb_model_pkg_run_job_id(self, ueb_model_pkg_CKAN_resource_id, run_job_id):
    
        """
        Updates a ueb model package request resource's 'extras' field to include
        RunJobID: param pkg_process_id
        Note that the extra field in resource table holds a json string

        param ueb_model_pkg_CKAN_resource_id: id of the resource to be updated
        param run_job_id: ueb run job id returned from app server responsible for running ueb
        @rtype: updated resource dictionary if successful otherwise None
        """
        # TODO: the following documentation needs to be updated to match the parameters of this function
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
        # For example, as shown below, we are storing a vlaue for PackageProcessJobID
        # which will be added/updated to the existing json string stored in the extras field

        data_dict = {'RunJobID': run_job_id}
        updated_resource = uebhelper.update_resource(ueb_model_pkg_CKAN_resource_id, data_dict)
        return updated_resource  
    
    def _update_ueb_model_pkg_run_status(self, ueb_model_pkg_CKAN_resource_id, status):
        # TODO: include docstring
        data_dict = {'UEBRunStatus': status}
        updated_resource = uebhelper.update_resource(ueb_model_pkg_CKAN_resource_id, data_dict)
        return updated_resource