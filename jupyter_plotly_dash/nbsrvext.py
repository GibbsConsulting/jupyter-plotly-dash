'''
Server extension for jupyter-plotly-dash
'''

from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler

class JPDHandler(IPythonHandler):
    def get(self):
        self.finish("Got JPHandled")
    def post(self):
        self.finish("Got JPHandled postically")

def load_jupyter_server_extension(nb_app):

    web_app = nb_app.web_app
    print("LOading with webapp")
    print(web_app)
    print(web_app.settings)
    for k,v in web_app.settings.items():
        print(k,v)

    host_pattern = '.*$'
    route_pattern = url_path_join(web_app.settings['base_url'], '/fluptastic')
    web_app.add_handlers(host_pattern,
                         [(route_pattern,
                           JPDHandler)])

def _jupyter_server_extension_paths():
    return [{
        "module" : "jupyter_plotly_dash.nbsrvext"
        }]
