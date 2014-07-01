import ckan.plugins as p
import ckan.lib.base as base
from apscheduler.scheduler import Scheduler
from ckan.common import c
import ckan.lib.helpers as h 
import tasks 
import os
import logging
import ckan.model.meta as meta
import threading
import time

log = logging.getLogger('ckan.logic')


# TODO: delete this class as we are no more using any background tasks in CKAN 2.2
class UEBScheduler(object):
    @classmethod
    def run_apcheduler(self):
        scheduler = Scheduler()
        scheduler.coalesce = True
        scheduler.start()
        source = 'uebpackage.plugin.run_scheduler.run_jobs():'
        # set the interval to half the time of actual interval at which you want the job to run
        # the scheduler will miss a job run between every 2 actual runs. The log will show a message like
        # "skipped: maximum number of running instances reached (1)" each time it misses a run.
        # That's why the interval is set to half of the actual interval we want the job to run.
        # Note this should always be set to 15 to get an interval of 30 min.
        # the job actually will be run at an interval of interval * 2 minutes
        interval = 15

        @scheduler.interval_schedule(minutes=interval)  # @scheduler.interval_schedule(minutes=interval, max_instances=1)
        def run_jobs():
            lock = threading.RLock()
            lock.acquire()
            session = meta.Session
            log.info(source + 'Started scheduled background jobs')

            # add task is for debug
            total = tasks.add(2, 3)
            print total

            try:
                log.info(source + "Checking ueb model build request status")
                from routes import request_config
                from routes.mapper import Mapper
                config = request_config()
                config.mapper = Mapper()
                config.host = '127.0.0.1:5000'
                config.protocol = 'http'
                #if hasattr(config, 'using_request_local'):
                config.request_local = tasks.check_ueb_request_process_status()
                config = request_config()
                    #tasks.check_ueb_request_process_status()
                log.info(source + "UEB model build request status check finished")
            except Exception as e:
                log.error(source + 'Failed to check ueb package build request status.\nException:%s' % e)
                pass
            try:
                log.info(source + "Retrieving ueb model package from app server")
                tasks.retrieve_ueb_packages()
                log.info(source + "Retrieving ueb model package from app server was successful")
            except Exception as e:
                log.error(source + 'Failed to retrieve ueb package from app server.\nException:%s' % e)
                pass

            try:
                log.info(source + "Checking ueb model run status")
                tasks.check_ueb_run_status()
                log.info(source + "UEB model run status check finished")
            except Exception as e:
                log.error(source + 'Failed to check ueb package run status.\nException:%s' % e)
                pass
            try:
                log.info(source + "Retrieving ueb model output package from app server")
                tasks.retrieve_ueb_run_output_packages()
                log.info(source + "Retrieving ueb model output package from app server was successful")
            except Exception as e:
                log.error(source + 'Failed to retrieve ueb model output package from app server.\nException:%s' % e)
                pass

            session.remove()
            log.info(source + 'Finished scheduled background jobs')
            time.sleep(interval * 60)
            lock.release()


def uebpackage_build_main_navigation(*args):
    output = h.build_nav_main(*args)
    # show ciwater related menu options only if the user is loggedin
    if c.user:        
        link_pkg = h.url_for(controller='ckanext.uebpackage.controllers.packagecreate:PackagecreateController', action='packagecreateform')
        link_run = h.url_for(controller='ckanext.uebpackage.controllers.uebexecute:UEBexecuteController', action='select_model_package')
        if p.toolkit.c.action == 'packagecreateform' or p.toolkit.c.action == 'select_model_package':
            menu = h.literal('<li class="dropdown">')
        else:
            menu = h.literal('<li class="dropdown">')
        
        menu += h.literal('<a id="drop1" role="button" data-toggle="dropdown"  class="dropdown-toggle" href="#">')
        menu += 'UEB' + h.literal('<b><span class="caret"></span></b>')
        menu += h.literal('</a>')
        menu += h.literal('<ul class="dropdown-menu" role="menu" area-labelledby="drop1">')
                
        li = h.literal('<li role="presentation"><a role="menuitem" tabindex="-1" href=') + link_pkg + h.literal('>UEB Model Package</a>') + h.literal('</li>')
        menu += li
        
        li = h.literal('<li role="presentation"><a role="menuitem" tabindex="-1" href=') + link_run + h.literal('>Run UEB</a>') + h.literal('</li>')
        menu += li
        menu += h.literal('</ul>')
        menu += h.literal('</li>')

        output = menu + output
                
    return output


def get_package_extras(pkg_id):
    context = {'model': base.model, 'session': base.model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
    data_dict = {'id': pkg_id}
    package = p.toolkit.get_action('package_show')(context, data_dict)
    return package['extras']

class UebPackagePlugins(p.SingletonPlugin):
    # Set inherit=True so that we don't have to implement all functions of this interface
    p.implements(p.IRoutes, inherit=True) 
    p.implements(p.IConfigurer)   
    p.implements(p.ITemplateHelpers, inherit=True)
    
    #Ref: http://docs.ckan.org/sq/latest/resources.html#resources-within-extensions
    p.toolkit.add_resource('public', 'uebresources')    
    
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
                                      'uebpackage', 'public')
        config['extra_public_paths'] = ','.join([our_public_dir,
                config.get('extra_public_paths', '')])

    # Update CKAN's map settings, see the IRoutes plugin interface.
    def before_map(self, map):
        # Here create route shortcuts to all your extension's controllers and their actions
        map.connect('/uebpackage/createform',
                    controller='ckanext.uebpackage.controllers.packagecreate:PackagecreateController',
                    action='packagecreateform')
        map.connect('/uebpackage/createformsubmit', controller='ckanext.uebpackage.controllers.packagecreate:PackagecreateController', action='submit')
        map.connect('/uebpackage/selectpackagetoexecute', controller='ckanext.uebpackage.controllers.uebexecute:UEBexecuteController', action='select_model_package')
        map.connect('/uebpackage/ueb_execute/{pkg_id}', controller='ckanext.uebpackage.controllers.uebexecute:UEBexecuteController', action='execute')
        map.connect('/uebpackage/ueb_execute_status/{pkg_id}', controller='ckanext.uebpackage.controllers.uebexecute:UEBexecuteController', action='check_package_run_status')
        map.connect('/uebpackage/check_package_build_status/{pkg_id}', controller='ckanext.uebpackage.controllers.packagecreate:PackagecreateController', action='check_package_build_status')
        map.connect('/uebpackage/retrieve_input_package/{pkg_id}', controller='ckanext.uebpackage.controllers.packagecreate:PackagecreateController', action='retrieve_input_package')
        map.connect('/uebpackage/retrieve_output_package/{pkg_id}', controller='ckanext.uebpackage.controllers.uebexecute:UEBexecuteController', action='retrieve_output_package')
        return map

    # ITemplateHelpers method implementation
    def get_helpers(self):
        
        # Template helper function names (e.g: 'uebpackage_build_nav_main')should begin with the name of the
        # extension they belong to, to avoid clashing with functions from
        # other extensions.
        return {'uebpackage_build_nav_main': uebpackage_build_main_navigation,
                'get_package_extras': get_package_extras}

    # TODO: delete the following one comment line
    #UEBScheduler.run_apcheduler()