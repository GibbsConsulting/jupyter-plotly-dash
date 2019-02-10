#
#    __init__.py
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

from ..nbsrvext import do_load_jupyter_server_extension

def _jupyter_server_extension_paths():
    return [{
        "module" : "jupyter_plotly_dash.serverext"
        }]

def load_jupyter_server_extension(nb_app):
    return do_load_jupyter_server_extension(nb_app)
