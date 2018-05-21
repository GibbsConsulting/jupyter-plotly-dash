from .async_views import AsyncViews, get_global_av
from django_plotly_dash import DjangoDash

class JupyterDash:
    def __init__(self, name, gav=None, width=800, height=600):
        self.dd = DjangoDash(name)
        self.gav = gav and gav or get_global_av()
        self.gav.add_app(self, name)
        self.width = width
        self.height = height
        self.add_external_link = True
        self.session_state = dict()
        self.app_state = dict()
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
    def get_app_root_url(self):
        return 'http://localhost:%i%s' % (self.gav.port, self.get_base_pathname(self.dd._uid))

    def _repr_html_(self):
        url = self.get_app_root_url()
        external = self.add_external_link and '<hr/><a href="{url}" target="_new">Open in new window</a>'.format(url=url) or ""
        iframe = '''<div>
  <iframe src="{url}" width={width} height={height}></iframe>
  {external}
</div>'''.format(url = url,
                 external = external,
                 width = self.width,
                 height = self.height)
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

