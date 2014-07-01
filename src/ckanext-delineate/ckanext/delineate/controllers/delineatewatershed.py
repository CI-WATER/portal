__author__ = 'pabitra'
import ckan.lib.base as base
import logging
import ckan.plugins as p
from ckan.controllers import storage
from datetime import datetime
from ckan.common import _
import ckan.lib.uploader as uploader
import ckan.lib.munge as munge
import os
import shutil
import httplib
import zipfile
import glob
import time
from .. import helpers as d_helper

tk = p.toolkit
_ = tk._  # translator function

log = logging.getLogger('ckan.logic')


class DelineatewatershedController(base.BaseController):

    def show_form(self):
        errors = {}
        data = {}
        error_summary = {}
        form_vars = {'data': data, 'errors': errors, 'error_summary': error_summary}
        tk.c.is_checkbox_checked = False
        tk.c.shape_file_exists = False
        return tk.render('watershed_delineate_form.html', extra_vars=form_vars)

    def submit(self):
        if "delineate" in tk.request.params:
            lat = tk.request.params['lat']
            lon = tk.request.params['lon']
            
            return self._send_delineation_request_to_app_server(lat, lon)
    
    def delineate_ws(self, lat, lon):
        """
        This is designed to be called as ajax call
        """
        return self._send_delineation_request_to_app_server(lat, lon)
               
    def showWatershed(self, shapeFileType):
        if shapeFileType:
            return self._send_latlon_values_request_to_app_server(shapeFileType) 
          
    def downloadshapefile(self):
        # zip all files with name matching to shapeFileType
        source = 'delineate.delineatewatershed.downloadshapefile():'
        ckan_default_dir = d_helper.StringSettings.ckan_user_session_temp_dir
        session_id = base.session['id']  # base.session.id
        shape_files_source_dir = os.path.join(ckan_default_dir, session_id, 'ShapeFiles')
        target_zip_dir = os.path.join(ckan_default_dir, session_id, 'ShapeZippedFile')
        shape_zip_filename = d_helper.StringSettings.ckan_delineated_watershed_download_filename
        shape_zip_file = os.path.join(target_zip_dir, shape_zip_filename)
        
        if not os.path.isdir(shape_files_source_dir):
            log.error(source + 'CKAN error: Expected shape file source dir path (%s) is missing.'
                      % shape_files_source_dir)

            tk.abort(400, _('Expected shape files source dir path is missing.'))
            return
        
        try:
            if os.path.isdir(target_zip_dir):
                shutil.rmtree(target_zip_dir)
            
            os.makedirs(target_zip_dir)
            files_to_archive = shape_files_source_dir + '/' + 'Watershed.*'
            zipper = zipfile.ZipFile(shape_zip_file, 'w')
            for file_to_zip in glob.glob(files_to_archive):
                zipper.write(file_to_zip, os.path.basename(file_to_zip), compress_type=zipfile.ZIP_DEFLATED)
            
            zipper.close()
            
            file_size = os.path.getsize(shape_zip_file)            
            base.response.headers['Content-Type'] = 'application/octet-stream'
            base.response.headers['Content-Disposition'] = 'attachment; filename=Watershed.zip'
            base.response.headers['Content-Length'] = file_size
            base.response.headers['Content-Encoding'] = 'binary'
            
            with open(shape_zip_file, 'r') as file_obj:
                file_data = file_obj.read()    
                base.response.body = file_data
            
            base.response.status_int = 200    
                         
        except Exception as e:       
            log.error(source + 'CKAN error: %s' % e)
            #tk.abort(400, _('CKAN error: %s' % e))
            base.response.body = 'CKAN shape file download error'
            base.response.status_int = 404

    def saveshapefile(self, lat, lon, shape_file_name, watershed_des, organization):
        return self._save_shape_file_as_resource(lat, lon, shape_file_name, watershed_des, organization)
        
    def _save_shape_file_as_resource(self, lat, lon, shape_file_name, watershed_des, organization):
        source = 'delineate.delineatewatershed._save_shape_file_as_resource():'
        ajax_response = d_helper.AJAXResponse()

        if not self._validate_file_name(shape_file_name):
            ajax_response.success = False
            ajax_response.message = 'Invalid shape file name:%s.' % shape_file_name + '\nFile name needs to have only ' \
                                                                                      'alphanumeric characters and ' \
                                                                                      'dash, hyphen or space characters.'
            return ajax_response.to_json()

        # TODO: make the saving of the file to temp directory a separate function
        ckan_default_dir = d_helper.StringSettings.ckan_user_session_temp_dir
        session_id = base.session['id']
        shape_files_source_dir = os.path.join(ckan_default_dir, session_id, 'ShapeFiles')
        target_zip_dir = os.path.join(ckan_default_dir, session_id, 'ShapeZippedFile') 
        shape_zip_file = os.path.join(target_zip_dir, shape_file_name + '.zip')

        if not os.path.isdir(shape_files_source_dir):
            log.error(source + 'CKAN error: Expected shape file source dir path (%s) is missing.'
                      % shape_files_source_dir)

            ajax_response.success = False
            ajax_response.message = _('Failed to save the watershed shape file.')
            return ajax_response.to_json()

        if not os.path.exists(shape_zip_file):
            #create the watershed zip file first
            if os.path.isdir(target_zip_dir):
                shutil.rmtree(target_zip_dir)
            
            os.makedirs(target_zip_dir)
            files_to_archive = shape_files_source_dir + '/' + 'Watershed.*'
            zipper = zipfile.ZipFile(shape_zip_file, 'w')
            for file_to_zip in glob.glob(files_to_archive):
                zipper.write(file_to_zip, os.path.basename(file_to_zip), compress_type=zipfile.ZIP_DEFLATED)
            
            zipper.close()

        # TODO: make the creation of a new package a new function
        # create a package
        package_create_action = tk.get_action('package_create')
        
        # create unique package name using the current time stamp as a postfix to any package name
        unique_postfix = datetime.now().isoformat().replace(':', '-').replace('.', '-').lower()
        pkg_title = shape_file_name  # + '_'
        pkg_name = shape_file_name.replace(' ', '-').lower()
        data_dict = {
                    'name': pkg_name + '_' + unique_postfix,
                    'type': 'geographic-feature-set',
                    'title': pkg_title,
                    'author': tk.c.userObj.name if tk.c.userObj else tk.c.author,   # TODO: userObj is None always. Need to retrieve user full name
                    'notes': 'This is a dataset that contains a watershed shape zip file for an outlet'
                             ' location at latitude:%s and longitude:%s. ' % (lat, lon) + watershed_des,
                    'owner_org': organization,
                    'variable_name': '',  # extra metadata field begins from here
                    'variable_unit': '',
                    'north_extent': '',
                    'south_extent': '',
                    'east_extent': '',
                    'west_extent': '',
                    'projection': 'WGS_1984',   # this what our delineation service sets for the watershed
                    'dataset_type': 'geographic-feature-set'
                    }
        
        context = {'model': base.model, 'session': base.model.Session, 'user': tk.c.user or tk.c.author, 'save': 'save'}
        try:
            pkg_dict = package_create_action(context, data_dict)
            log.info(source + 'A new dataset was created with name: %s' % data_dict['title'])
        except Exception as e:
            log.error(source + 'Failed to create a new dataset for saving watershed shape file as'
                               ' a resource.\n Exception: %s' % e)

            ajax_response.success = False
            ajax_response.message = _('Failed to create a new dataset for'
                                      ' saving watershed shape file as a resource.')
            return ajax_response.to_json()

        # TODO: make the add resource to a package a new function
        if not 'resources' in pkg_dict:
            pkg_dict['resources'] = []

        file_name = munge.munge_filename(shape_file_name + '.zip')
        resource = {'url': file_name, 'url_type': 'upload'}
        upload = uploader.ResourceUpload(resource)
        upload.filename = file_name
        upload.upload_file = open(shape_zip_file, 'r')
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
            log.error(source + 'Failed to update the new dataset for adding watershed shape file as'
                               ' a resource.\n Exception: %s' % e)

            ajax_response.success = False
            ajax_response.message = _('Failed to save watershed shape file as a resource.')
            return ajax_response.to_json()

        # Get out resource_id resource from model as it will not appear in
        # package_show until after commit
        upload.upload(context['package'].resources[-1].id, uploader.get_max_resource_size())
        base.model.repo.commit()
        ajax_response.success = True
        ajax_response.message = _('Watershed shape file was saved as a resource.')
        return ajax_response.to_json()

    def _send_latlon_values_request_to_app_server(self, shapeFileType):
        source = 'delineate.delineatewatershed._send_latlon_values_request_to_app_server():'

        ajax_response = d_helper.AJAXResponse()

        # zip all files with name matching to shapeFileType
        ckan_default_dir = d_helper.StringSettings.ckan_user_session_temp_dir
        session_id = base.session['id']  # base.session.id
        shape_files_source_dir = os.path.join(ckan_default_dir, session_id, 'ShapeFiles')
        target_zip_dir = os.path.join(ckan_default_dir, session_id, 'ShapeZippedFile') 
        shape_zip_file = os.path.join(target_zip_dir, shapeFileType + '.zip')
        
        if not os.path.isdir(shape_files_source_dir):
            log.error(source + 'CKAN error: Expected shape file source dir path (%s) '
                               'is missing.' % shape_files_source_dir)
            ajax_response.success = False
            ajax_response.message = 'CKAN error:Expected shape files source dir path is missing.'
            return ajax_response.to_json()

        try:
            if os.path.isdir(target_zip_dir):
                shutil.rmtree(target_zip_dir)
            
            os.makedirs(target_zip_dir)
            files_to_archive = shape_files_source_dir + '/' + shapeFileType + '.*'
            zip_it = zipfile.ZipFile(shape_zip_file, 'w')
            for shp_file in glob.glob(files_to_archive):
                zip_it.write(shp_file, os.path.basename(shp_file), compress_type=zipfile.ZIP_DEFLATED)
            
            zip_it.close()
            service_host_address = d_helper.StringSettings.app_server_host_address
            service_request_url = d_helper.StringSettings.app_server_api_get_shape_lat_lon_values_url
            connection = httplib.HTTPConnection(service_host_address)
            headers = {'Content-Type': 'application/text', 'Accept': 'application/text'}
            # get request data from the zip file
            with open(shape_zip_file, 'r') as file_obj:
                file_data = file_obj.read()    
                request_body_content = file_data
        except Exception as e:       
                log.error(source + ' CKAN error: %s' % e)
                ajax_response.success = False
                ajax_response.message = 'CKAN error:%s' % e
                return ajax_response.to_json()

        # Let's wait for 0.01 second before calling the web service
        # Otherwise sometime we get
        # 104 error - Connection Reset by Peer
        # ref: http://stackoverflow.com/questions/383738/104-connection-reset-by-peer-socket-error-or-when-does-closing-a-socket-resu
        time.sleep(0.01)
        # call the service
        connection.request('POST', service_request_url, request_body_content, headers)
                
        # retrieve response
        service_call_results = connection.getresponse()
        if service_call_results.status == httplib.OK:
            log.info(source + 'Lat/lon values obtained from app server')
            service_response_data = service_call_results.read()
            ajax_response.success = True
            ajax_response.message = 'Lat/lon values were obtained for the provided shape file.'
            ajax_response.json_data = service_response_data
            connection.close()
            return ajax_response.to_json()

        else:
            connection.close()
            log.error(source + 'App server error: Request to get lat/lon '
                               'values for a shape file failed: %s' % service_call_results.reason)
            ajax_response.success = False
            ajax_response.message = 'App server error: Request to get lat/lon ' \
                                    'values for a shape file failed: %s' % service_call_results.reason
            return ajax_response.to_json()

    def _send_delineation_request_to_app_server(self, lat, lon):        
        source = 'delineate.delineatewatershed.packagerequest.__send_delineation_request_to_app_server():'
        ajax_response = d_helper.AJAXResponse()
                
        tk.c.shape_file_exists = False
        service_host_address = d_helper.StringSettings.app_server_host_address
        qry_str = "?watershedOutletLat=" + lat + "&watershedOutletLon=" + lon
        service_request_url = d_helper.StringSettings.app_server_api_delineate_url + qry_str
                
        connection = httplib.HTTPConnection(service_host_address)
        # Let's wait for 0.01 second before calling the web service
        # Otherwise sometime we get
        # 104 error - Connection Reset by Peer
        # ref: http://stackoverflow.com/questions/383738/104-connection-reset-by-peer-socket-error-or-when-does-closing-a-socket-resu
        time.sleep(0.01)
        
        # call the service
        connection.request('GET', service_request_url, qry_str)
        # retrieve web service response
        service_call_results = connection.getresponse()
                
        if service_call_results.status == httplib.OK:
            ckan_default_dir = d_helper.StringSettings.ckan_user_session_temp_dir
            # create a directory for saving the shape zip file
            # this will be a dir in the form of: /tmp/ckan/{session_id}
            session_id = base.session.id
            destination_dir = os.path.join(ckan_default_dir, session_id)
            try:
                if os.path.isdir(destination_dir):
                    shutil.rmtree(destination_dir)

                os.makedirs(destination_dir)
            except Exception as e:
                log.error(source + 'Failed to either remove or create temporary dir:%s '
                                   'needed to save the shape zip file obtained from app server.\n '
                                   'Exception: %s' % (destination_dir, e))
                raise e

            shape_filename = d_helper.StringSettings.ckan_delineated_watershed_temporary_filename
            shapes_zipfile = os.path.join(destination_dir, shape_filename)
            
            bytes_to_read = 16 * 1024
            
            try:
                with open(shapes_zipfile, 'w') as file_obj:
                    while True:
                        data = service_call_results.read(bytes_to_read)
                        if not data:
                            break
                        file_obj.write(data)

                # Let's wait for a second to completely finish getting data from the
                # app server before we close the connection. Otherwise sometime we get
                # 104 error - Connection Reset by Peer
                # ref: http://stackoverflow.com/questions/383738/104-connection-reset-by-peer-socket-error-or-when-does-closing-a-socket-resu
                time.sleep(1)
                connection.close()
                tk.c.shape_file_exists = True
                base.session['id'] = base.session.id
                base.session.save()
                log.info(source + 'Saved the shape zip file at %s temporarily.' % destination_dir)
            except Exception as e:  
                connection.close()
                log.error(source + 'Failed to save the shape files sent by the app server.\n Exception: %s' % e)
                ajax_response.success = False
                ajax_response.message = 'CKAN Error:Failed to save the generated shape files.'                
                return ajax_response.to_json()
        else:
            connection.close()
            log.error(source + 'App server returned error:%s' % service_call_results.reason)
            ajax_response.success = False            
            ajax_response.message = 'App Server error:%s' % service_call_results.reason
            return ajax_response.to_json()
                       
        # unzip the saved shapefile.zip 
        if tk.c.shape_file_exists:
            unzip_dir_path = os.path.join(destination_dir, "ShapeFiles")   
            try:
                if os.path.isdir(unzip_dir_path):
                    shutil.rmtree(unzip_dir_path)

                os.makedirs(unzip_dir_path)
            except Exception as e:
                log.error(source + 'Failed to either remove or create temporary dir:%s '
                                   'needed to unzip the shape zip file obtained from app server.\n '
                                   'Exception: %s' % (destination_dir, e))
                raise e

            zipper = zipfile.ZipFile(shapes_zipfile)
            zipper.extractall(path=unzip_dir_path)
            log.info(source + 'Shape files saved in CKAN temporarily at:%s' % unzip_dir_path)  
        
        tk.c.outletLat = lat
        tk.c.outletLon = lon 
                
        ajax_response.success = True        
        ajax_response.message = 'Delineation successful.'
        return ajax_response.to_json()

    def _upload_file(self, file_path):
        """
        uploads a file to ckan filestore as and returns file metadata
        related to its existance in ckan
        param file_path: name of the file with its current location (path)
        """
        source = 'delineate.delineatewatershed._upload_file():'
        # this code has been implemented based on the code for the upload_handle() method
        # in storage.py    
        bucket_id = base.config.get('ckan.storage.bucket', 'default')    
        ts = datetime.now().isoformat().split(".")[0]  # '2010-07-08T19:56:47'    
        file_name = os.path.basename(file_path).replace(' ', '-')  # ueb request.txt -> ueb-request.txt
        file_key = os.path.join(ts, file_name) 
        label = file_key
        params = {}
        params['filename_original'] = os.path.basename(file_path)
        params['key'] = file_key
        try:
            with open(file_path, 'r') as file_obj:
                ofs = storage.get_ofs()
                resource_metadata = ofs.put_stream(bucket_id, label, file_obj, params)
                log.info(source + 'File upload was successful for file: %s' % file_path)
        except Exception as e:
            log.error(source + 'Failed to upload file: %s \nException %s' % (file_path, e))
            tk.abort(400, _('Failed to upload file: %s') % file_path)
           
        return resource_metadata 

    def _validate_file_name(self, file_name):
        """
        Validates file_name and returns true
        if it contains only alphanumeric chars and dash, hyphen or space
        characters. Otherwise returns false.
        """
        import string
        allowed_chars = string.ascii_letters + string.digits + '_-' + ' '
        file_name = string.strip(file_name)
        if len(file_name) == 0:
            return False
        
        return all(c in allowed_chars for c in file_name)       