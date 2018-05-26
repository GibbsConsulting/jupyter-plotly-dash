'''
Kernel-side code for passing info about JupyterDash applications to the server
'''

from ipykernel.comm import Comm

local_comms = {}

def locate_jpd_comm(da_id, app):
    global local_comms
    comm, callback = local_comms.get(da_id, (None, None) )
    if comm is None:
        comm = Comm(target_name='jpd_%s' %da_id,
                    data={'jpd_type':'inform',
                      'da_id':da_id})
        @comm.on_msg
        def callback(msg):
            comm.send({'jpd_type':'response',
                       'da_id':da_id,
                       'app':str(app),
                       'response':str(msg),
                       'mimetype':'nobody talks about mimetype'})
        local_comms[da_id] = comm, callback

    return comm
