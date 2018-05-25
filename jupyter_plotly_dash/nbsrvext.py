'''
Server extension for jupyter-plotly-dash
'''

from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler

from traitlets import Instance

class RequestRedirectionHandler(IPythonHandler):

    kernel_manager = Instance('notebook.services.kernels.kernelmanager.MappingKernelManager')

    registered_apps = {}

    def get(self, da_id=None, stem=None):
        args = {k:self.get_argument(k) for k in self.request.arguments}
        self.send_with_pause(da_id, stem, args, "GET")

    def post(self, da_id=None, stem=None):
        args = {k:self.get_argument(k) for k in self.request.arguments}
        self.send_with_pause(da_id, stem, args, "POST")

    def check_xsrf_cookie(self):
        # Override for this handler; post permitted as the alternatives with xsrf are too awkward to contemplate
        return

    def send_with_pause(self, da_id, stem, args, src_type):

        reg_app = RequestRedirectionHandler.registered_apps.get(da_id, {})
        print("Sending %s to %s" % (reg_app, da_id))

        self.finish("RequestRedirectionHandler [%s] [%s] args [%s] from [%s]" % (da_id, stem, args, src_type))

    @staticmethod
    def register_instance( da_id, args ):

        if da_id is None:
            return str(RequestRedirectionHandler.registered_apps)

        existing = RequestRedirectionHandler.registered_apps.get(da_id, None)

        if not existing:
            RequestRedirectionHandler.registered_apps[da_id] = args
            return "Added: %s" % str(args)

        return "Existing: %s" % str(existing)

class JPDHandler(IPythonHandler):

    def find_args(self):
        aVals = {}
        for arg in ['session_id','kernel_id','local_url',]:
            aVals[arg] = self.get_argument(arg, "<MISSING>")
        return aVals

    def get(self, da_id=None, **kwargs):
        args = self.find_args()
        self.finish(RequestRedirectionHandler.register_instance(da_id, args))

    def post(self, da_id=None, **kwargs):
        args = self.find_args()
        self.finish("Got JPHandled postically " + str(args))

def load_jupyter_server_extension(nb_app):

    web_app = nb_app.web_app
    print("LOading with webapp")
    print(web_app)
    print(web_app.settings)
    for k,v in web_app.settings.items():
        print(k,v)

    host_pattern = '.*$'

    root_endpoint = "/app/"
    print(url_path_join(web_app.settings['base_url'], '%(rep)sregister/(?P<da_id>\w+)' %{'rep':root_endpoint}))

    web_app.add_handlers(host_pattern,
                         [(url_path_join(web_app.settings['base_url'],
                                         '%(rep)sregister/(?P<da_id>\w+)' %{'rep':root_endpoint} ),
                           JPDHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '%(rep)sregistrants'%{'rep':root_endpoint} ),
                           JPDHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '%(rep)sendpoints/(?P<da_id>\w+)/(?P<stem>.*)'%{'rep':root_endpoint} ),
                           RequestRedirectionHandler),
                          (url_path_join(web_app.settings['base_url'],
                                         '%(rep)sendpoints/(?P<da_id>\w+)'%{'rep':root_endpoint} ),
                           RequestRedirectionHandler),
                          ])

def _jupyter_server_extension_paths():
    return [{
        "module" : "jupyter_plotly_dash.nbsrvext"
        }]
