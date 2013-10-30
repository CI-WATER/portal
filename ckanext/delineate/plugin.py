__author__ = 'pabitra'
import ckan.plugins as p
from routes import url_for
import ckan.lib.helpers as h
from ckan.common import c
import os
import logging

log = logging.getLogger('ckan.logic')


def delineate_build_main_navigation(*args):
    output = h.build_nav_main(*args)
    if c.user: 
        link = h.link_to('Delineate', h.url_for(controller='ckanext.delineate.controllers.delineatewatershed:DelineatewatershedController', action='show_form'))

        if p.toolkit.c.action == 'show_form':
            li = h.literal('<li class="active">') + link + h.literal('</li>')
        else:
            li = h.literal('<li>') + link + h.literal('</li>')

        output = li + output

    return output


class DelineateWatershedPlugins(p.SingletonPlugin):
    # Set inherit=True so that we don't have to implement all functions of this interface
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers, inherit=True)

    #Ref: http://docs.ckan.org/sq/latest/resources.html#resources-within-extensions
    p.toolkit.add_resource('public', 'delineate_resources')

    # Update CKAN's config settings, see the IConfigurer plugin interface.
    def update_config(self, config):

        # Tell CKAN to use the template files in
        # ckanext-uebpackage/ckanext/uebpackage/templates.
        p.toolkit.add_template_directory(config, 'templates')

        # add the extension's public dir path so that
        # ckan can find any resources used from this path
        # get the current dir path (here) for this plugin
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        our_public_dir = os.path.join(rootdir, 'ckanext',
                                      'delineate', 'public')
        config['extra_public_paths'] = ','.join([our_public_dir,
                config.get('extra_public_paths', '')])


    # Update CKAN's map settings, see the IRoutes plugin interface.
    def before_map(self, map):
        # Here create route shortcuts to all your extension's controllers and their actions
        map.connect('/delineate/show_map', controller='ckanext.delineate.controllers.delineatewatershed:DelineatewatershedController', action='show_form')
        map.connect('/delineate/submit', controller = 'ckanext.delineate.controllers.delineatewatershed:DelineatewatershedController', action='submit')
        map.connect('/delineate/delineate_ws/{lat}/{lon}', controller = 'ckanext.delineate.controllers.delineatewatershed:DelineatewatershedController', action='delineate_ws')
        map.connect('/delineate/showWatershed/{shapeFileType}', controller = 'ckanext.delineate.controllers.delineatewatershed:DelineatewatershedController', action='showWatershed')
        map.connect('/delineate/downloadshapefile', controller = 'ckanext.delineate.controllers.delineatewatershed:DelineatewatershedController', action='downloadshapefile')
        map.connect('/delineate/saveshapefile/{lat}/{lon}/{shape_file_name}/{watershed_des}', controller = 'ckanext.delineate.controllers.delineatewatershed:DelineatewatershedController', action='saveshapefile')
        return map

    #ITemplateHelpers method implementation
    def get_helpers(self):
        # Template helper function names (e.g: 'delineate_build_nav_main') should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.

        return {
            'delineate_build_nav_main': delineate_build_main_navigation
        }