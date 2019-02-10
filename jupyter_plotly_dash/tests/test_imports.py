'''
Test imports work
'''

#
#    test_imports.py
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

def test_wrapper_loading():
    'Test loading of wrapper module'
    from ..dash_wrapper import JupyterDash
    assert JupyterDash

def test_async_views_loading():
    'Test loading of async module'
    from ..async_views import AsyncViews
    assert AsyncViews

def test_ipython_loading():
    'Test loading of ipython module'
    from ..ipython import load_ipython_extension
    assert load_ipython_extension

def test_nbkernel_loading():
    'Test loading of nbkernel module'
    from ..nbkernel import locate_jpd_comm
    assert locate_jpd_comm

def test_nbsrvext_loading():
    'Test loading of nbsrvext module'
    from ..nbsrvext import wrapped_on_message
    assert wrapped_on_message

