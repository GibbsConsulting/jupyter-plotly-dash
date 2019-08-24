#
#    dash_wrapper.py
#
#    (c) Gibbs Consulting, a division of 0802100 (BC) Ltd, 2018
#
#    This file is part of jupyter-plotly-dash.
#
#    Jupyter-plotly-dash is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Jupyter-plotly-dash is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with jupyter-plotly-dash.  If not, see <https://www.gnu.org/licenses/>.
#

import uuid
import os

from .async_views import AsyncViews, get_global_av
from .nbkernel import locate_jpd_comm
from django_plotly_dash import DjangoDash
from django.conf import settings

try:
    # Try to load settings
    settings.configure()
except:
    pass

class JupyterDash:
    def __init__(self, name, gav=None, width=800, height=600):
        self.dd = DjangoDash(name)
        self.gav = gav and gav or get_global_av()
        self.gav.add_application(self, name)
        self.width = width
        self.height = height
        self.frame = False
        self.add_external_link = True
        self.session_state = dict()
        self.app_state = dict()
        self.local_uuid = str(uuid.uuid4()).replace('-','')
        self.use_nbproxy = False
    def as_dash_instance(self, specific_identifier=None, base_pathname=None):

        if base_pathname is None:
            base_pathname = self.get_base_pathname(specific_identifier)
            specific_identifier = self.session_id()
        else:
            if base_pathname[0] != '/':
                base_pathname = "/%s" % base_pathname
            if base_pathname[-1] != '/':
                base_pathname = "%s/" % base_pathname

        # TODO perhaps cache this. If so, need to ensure updated if self.app_state changes
        return self.dd.form_dash_instance(replacements=self.app_state,
                                          ndid = specific_identifier,
                                          base_pathname = base_pathname)

    def get_session_state(self):
        return self.session_state

    def set_session_state(self, state):
        self.session_state = state

    def handle_current_state(self):
        # Do nothing, at least for the moment...
        pass

    def update_current_state(self, wid, name, value):
        wd = self.app_state.get(wid,None)
        if wd is None:
            wd = dict()
            self.app_state[wid] = wd
        wd[name] = value

    def have_current_state_entry(self, wid, name):
        wd = self.app_state.get(wid,{})
        entry = wd.get(name,None)
        return entry is not None

    def get_base_pathname(self, specific_identifier):
        the_id = specific_identifier and specific_identifier or self.session_id()
        if self.use_nbproxy:
            # TODO this should be the_id not the uid?
            return '/proxy/%i/%s/' %(self.gav.port, self.dd._uid)
        return "/app/endpoints/%s/" % the_id

    def session_id(self):
        return self.local_uuid

    def get_app_root_url(self):

        # Local (not binder use) determined by presence of server prefix
        jh_serv_pref = os.environ.get('JUPYTERHUB_SERVICE_PREFIX',None)

        if jh_serv_pref is None:
            # Local use, root is given by proxy flag
            return self.get_base_pathname(self.session_id())

        # Running on a binder or similar
        # TODO restrict use of use_nbproxy here
        return "%s%s" %(jh_serv_pref, self.get_base_pathname(self.session_id())[1:])

    def __html__(self):
        return self._repr_html_()
    def _repr_html_(self):
        url = self.get_app_root_url()
        da_id = self.session_id()
        comm = locate_jpd_comm(da_id, self, url[1:-1])
        external = self.add_external_link and '<hr/><a href="{url}" target="_new">Open in new window</a> for {url}'.format(url=url) or ""
        fb = 'frameborder="%i"' %(self.frame and 1 or 0)
        iframe = '''<div>
  <iframe src="%(url)s" width=%(width)s height=%(height)s %(frame)s></iframe>
  %(external)s
</div>''' %{'url' : url,
            'da_id' : da_id,
            'external' : external,
            'width' : self.width,
            'height' : self.height,
            'frame': fb,}
        return iframe
    def callback(self, *args, **kwargs):
        return self.dd.callback(*args,**kwargs)
    def expanded_callback(self, *args, **kwargs):
        return self.dd.expanded_callback(*args,**kwargs)
    def _get_layout(self):
        return self.dd.layout
    def _set_layout(self, layout):
        self.dd.layout = layout
    layout = property(_get_layout, _set_layout)


    def process_view(self, view_name, args, app_path):
        if view_name == None:
            view_name = ''
        view_name = view_name.replace('-','_')
        view_name_parts = view_name.split('/')
        view_name = view_name_parts[0]
        func = getattr(self,'rv_%s'%view_name, None)
        if func is not None:
            # TODO process app_path if needed
            return func(args, app_path, view_name_parts)
        return ("<html><body>Unable to understand view name of %s with args %s and app path %s</body></html>" %(view_name, args, app_path),"text/html")

    def rv_(self, args, app_path, view_name_parts):
        if True and False:
            return ("<html><budy> App Path is [%s] </body></html>"%app_path,"text/html")
        mFunc = self.as_dash_instance(base_pathname=app_path).locate_endpoint_function()
        response = mFunc()
        return(response,"text/html")

    def rv__dash_layout(self, args, app_path, view_name_parts):
        dapp = self.as_dash_instance(base_pathname=app_path)
        with dapp.app_context():
            mFunc = dapp.locate_endpoint_function('dash-layout')
            resp = mFunc()
            body, mimetype = dapp.augment_initial_layout(resp)
            return (body, mimetype)

    def rv__dash_dependencies(self, args, app_path, view_name_parts):
        dapp = self.as_dash_instance(base_pathname=app_path)
        with dapp.app_context():
            mFunc = dapp.locate_endpoint_function('dash-dependencies')
            resp = mFunc()
            return (resp.data.decode('utf-8'), resp.mimetype)

    def rv__dash_update_component(self, args, app_path, view_name_parts):
        dapp = self.as_dash_instance(base_pathname=app_path)
        if dapp.use_dash_dispatch():
            mFunc = dapp.locate_endpoint_function('dash-update-component')
            import flask
            with dapp.test_request_context():
                flask.request._cached_json = (args, flask.request._cached_json[True])
                resp = mFunc()
        else:
            # Use direct dispatch with extra arguments in the argMap
            app_state = self.get_session_state()
            app_state['call_count'] = app_state.get('call_count',0) + 1
            argMap = {}
            argMap = {'dash_app_id': self.local_uuid,
                      'dash_app': self,
                      'user': None,
                      'session_state': app_state}
            resp = dapp.dispatch_with_args(args, argMap)
            self.set_session_state(app_state)
            self.handle_current_state()

        try:
            rdata = resp.data
            rtype = resp.mimetype
        except:
            rdata = resp
            rtype = "application/json"

        return (rdata, rtype)

    def rv__dash_component_suites(self, args, app_path, view_name_parts):
        return ("<html><body>Requested %s at %s with %s</body></html>" %(args,app_path,view_name_parts),"text/html")
