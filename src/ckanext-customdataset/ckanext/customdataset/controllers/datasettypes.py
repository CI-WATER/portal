__author__ = 'pabitra'
import ckan.lib.base as base
import ckan.lib.helpers as h
import logging
import ckan.plugins as p

tk = p.toolkit
_ = tk._  # translator function

log = logging.getLogger('ckan.logic')


class DatasetTypesController(base.BaseController):

    def select_dataset_types(self, environ, start_response):
        #start_response('200 OK', [('Content-type','text/plain')])
        #environ['HTTP_REFERER'] = 'http://127.0.0.1:5000/datatset_types'
        #h.redirect_to('package/dataset_types_form.html')
        return tk.render('dataset_types_form.html', extra_vars={})