'''
Kernel-side code for passing info about JupyterDash applications to the server
'''

#
#    nbkernel.py
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

from ipykernel.comm import Comm

local_comms = {}

def locate_jpd_comm(da_id, app, app_path):
    global local_comms
    comm = local_comms.get(da_id, None )
    if comm is None:
        comm = Comm(target_name='jpd_%s' %da_id,
                    data={'jpd_type':'inform',
                      'da_id':da_id})
        @comm.on_msg
        def callback(msg, app=app, da_id=da_id, app_path=app_path):
            # TODO see if app and da_id args needed for this closure
            content = msg['content']
            data = content['data']
            stem = data['stem']
            args = data['args']

            #app_path = "app/endpoints/%s" % da_id

            response, mimetype = app.process_view(stem, args, app_path)

            comm.send({'jpd_type':'response',
                       'da_id':da_id,
                       'app':str(app),
                       'response':response,
                       'mimetype':mimetype})
        local_comms[da_id] = comm

    return comm
