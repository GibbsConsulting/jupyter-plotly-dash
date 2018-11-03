from ..nbsrvext import do_load_jupyter_server_extension

def _jupyter_server_extension_paths():
    return [{
        "module" : "jupyter_plotly_dash.serverext"
        }]

def load_jupyter_server_extension(nb_app):
    return do_load_jupyter_server_extension(nb_app)
