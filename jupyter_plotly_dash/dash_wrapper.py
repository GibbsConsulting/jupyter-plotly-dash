from .async_views import AsyncViews, get_global_av
from .nbkernel import locate_jpd_comm
from django_plotly_dash import DjangoDash
import uuid

class JupyterDash:
    def __init__(self, name, gav=None, width=800, height=600):
        self.dd = DjangoDash(name)
        self.gav = gav and gav or get_global_av()
        self.gav.add_application(self, name)
        self.width = width
        self.height = height
        self.add_external_link = True
        self.session_state = dict()
        self.app_state = dict()
        self.local_uuid = str(uuid.uuid4()).replace('-','')
    def as_dash_instance(self, specific_identifier=None):
        # TODO perhaps cache this. If so, need to ensure updated if self.app_state changes
        return self.dd.form_dash_instance(replacements=self.app_state,
                                          specific_identifier=specific_identifier)

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
        return '/%s/' % specific_identifier
    def session_id(self):
        return self.local_uuid
    def get_app_root_url(self):
        if True:
            return "/app/endpoints/%s/" % (self.session_id())
        return 'http://localhost:%i%s' % (self.gav.port, self.get_base_pathname(self.dd._uid))

    def _repr_html_(self):
        url = self.get_app_root_url()
        da_id = self.session_id()
        comm = locate_jpd_comm(da_id, self)
        external = self.add_external_link and '<hr/><a href="{url}" target="_new">Open in new window</a>'.format(url=url) or ""
        iframe = '''<div>
        <script>
var kernel = require("base/js/namespace").notebook.kernel;
var session_id = kernel.session_id;

$.ajax({url:"/app/register/%(da_id)s",
        method:"GET",
        data:{session_id:kernel.session_id,
              kernel_id:kernel.id},
        success:function(result) {
console.log("Got ajax fluptasticness");
}}).always(function(response){
console.log("Always response");
console.log(response);
})
;
</script>
<iframe src="%(url)s" width=%(width)s height=%(height)s></iframe>
  {external}
</div>''' %{'url' : url,
            'da_id' : da_id,
            'external' : external,
            'width' : self.width,
            'height' : self.height}
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
        view_name = view_name.replace('-','_')
        func = getattr(self,'rv_%s'%view_name, None)
        if func is not None:
            # TODO process app_path if needed
            return func(args, app_path)
        return ("<html><body>Unable to understand view name of %s with args %s</body></html>" %(view_name, args),"text/html")

    def rv_(self, args, app_path):
        mFunc = self.as_dash_instance(specific_identifier=app_path).locate_endpoint_function()
        response = mFunc()
        return(response,"text/html")

    def rv__dash_layout(self, args, app_path):
        dapp = self.as_dash_instance(specific_identifier=app_path)
        with dapp.app_context():
            mFunc = dapp.locate_endpoint_function('dash-layout')
            resp = mFunc()
            body, mimetype = dapp.augment_initial_layout(resp)
            return (body, mimetype)

    def rv__dash_dependencies(self, args, app_path):
        dapp = self.as_dash_instance(specific_identifier=app_path)
        with dapp.app_context():
            mFunc = dapp.locate_endpoint_function('dash-dependencies')
            resp = mFunc()
            return (resp.data.decode('utf-8'), resp.mimetype)

    def rv__dash_update_component(self, args, app_path):
        dapp = self.as_dash_instance(specific_identifier=app_path)
        if dapp.use_dash_dispatch():
            mFunc = dapp.locate_endpoint_function('dash-update-component')
            import flask
            with dapp.test_request_context():
                flask.request._cached_json = (args, flask.request._cached_json[True])
                resp = mFunc()
        else:
            # Use direct dispatch with extra arguments in the argMap
            app_state = self.get_session_state()
            argMap = {}
            argMap = {'dash_app_id': self.local_uuid,
                      'dash_app': self,
                      'user': None,
                      'session_state': app_state}
            resp = dapp.dispatch_with_args(args, argMap)
            self.set_session_state(app_state)
            self.handle_current_state()

        return (resp.data.decode('utf-8'), resp.mimetype)

