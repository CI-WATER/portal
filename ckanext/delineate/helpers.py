class AJAXResponse(object):

    def __init__(self):
        self.success = False
        self.message = ''
        self.json_data = ''

    def to_json(self):
        fields = []

        for field in vars(self):
            fields.append(field)
        
        d = {}
        for attr in fields:
            d[attr] = getattr(self, attr)

        import simplejson
        return simplejson.dumps(d)


class StringSettings(object):
    ckan_user_session_temp_dir = '/tmp/ckan'
    ckan_delineated_watershed_download_filename = 'Watershed.zip'
    ckan_delineated_watershed_temporary_filename = 'shapefiles.zip'
    app_server_host_address = 'thredds-ci-water.bluezone.usu.edu'
    app_server_api_get_shape_lat_lon_values_url = '/api/ShapeLatLonValues'
    app_server_api_delineate_url = '/api/EPADelineate'