__author__ = 'pabitra'
from pylons import c
from ckan import model, logic
import ckan.plugins as p

import os
import logging

log = logging.getLogger('ckan.logic')


def most_recently_changed_packages_html():
    context = {'model': model, 'session': model.Session, 'user': c.user}
    data_dict = {'limit': 5}
    return logic.get_action('recently_changed_packages_activity_list_html')(
        context, data_dict)


class CustomizationPlugins(p.SingletonPlugin):
    # Set inherit=True so that we don't have to implement all functions of this interface
    p.implements(p.IRoutes, inherit=True)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers, inherit=True)

    #Ref: http://docs.ckan.org/sq/latest/resources.html#resources-within-extensions
    p.toolkit.add_resource('public', 'customization_resources')

    # Update CKAN's config settings, see the IConfigurer plugin interface.
    def update_config(self, config):

        # Tell CKAN to use the template files in
        # ckanext-customization/ckanext/customization/templates.
        p.toolkit.add_template_directory(config, 'templates')

        # add the extension's public dir path so that
        # ckan can find any resources used from this path
        # get the current dir path (here) for this plugin
        here = os.path.dirname(__file__)
        rootdir = os.path.dirname(os.path.dirname(here))
        our_public_dir = os.path.join(rootdir, 'ckanext',
                                      'customization', 'public')
        config['extra_public_paths'] = ','.join([our_public_dir,
                config.get('extra_public_paths', '')])

    def before_map(self, map):
        # Here create route shortcuts to all your extension's controllers and their actions
        #map.connect('/dataset_types', controller='ckanext.customization.controllers.datasettypes:DatasetTypesController', action='select_dataset_types')
        return map

    def get_helpers(self):
        '''Register the most_recently_changed_packages_html() function above as a template
        helper function.

        '''
        # Template helper function names should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {
            'customization_most_recently_changed_packages_html': most_recently_changed_packages_html
            }
