from .async_views import AsyncViews, get_global_av
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
    def as_dash_instance(self):
        # TODO perhaps cache this. If so, need to ensure updated if self.app_state changes
        return self.dd.form_dash_instance(replacements=self.app_state)

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
        local_url = 'http://localhost:%i%s' % (self.gav.port, self.get_base_pathname(self.dd._uid))
        da_id = self.session_id()
        external = self.add_external_link and '<hr/><a href="{url}" target="_new">Open in new window</a>'.format(url=url) or ""
        iframe = '''<div>
        <script>
var kernel = require("base/js/namespace").notebook.kernel;
var session_id = kernel.session_id;

$.ajax({url:"/app/register/%(da_id)s",
        method:"GET",
        data:{session_id:kernel.session_id,
              local_url:"%(local_url)s",
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
            'local_url' : local_url,
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

