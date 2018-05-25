'''
Server extension for jupyter-plotly-dash
'''

from notebook.utils import url_path_join
from notebook.base.handlers import IPythonHandler

from notebook.services.kernels.handlers import ZMQChannelsHandler

from traitlets import Instance

from tornado import gen

import json
import uuid

current_get = ZMQChannelsHandler.get
current_on_message = ZMQChannelsHandler.on_message
current_on_reply = ZMQChannelsHandler._on_zmq_reply

@gen.coroutine
def wrapped_get(self, kernel_id):
    print("In wrapped get")
    yield current_get(self, kernel_id)

def wrapped_on_message(self, msg):

    m2 = None

    if isinstance(msg, bytes):
        # for now, ignore binary messages
        pass
    else:
        deser_msg = json.loads(msg)
        channel = deser_msg.get('channel',None)
        #print("On message, channel is [%s]" % channel)
        header = deser_msg['header']
        msg_type = header.get('msg_type',"")
        if msg_type == 'comm_open' or msg_type == 'comm_msg':
            session = header['session']
            content = deser_msg['content']
            comm_id = content['comm_id']
            target_name = content.get('target_name',None)
            if target_name is not None:
                print("Comm msg with target name [%s]" % target_name)
            print("Comm msg with id [%s] and msg id [%s]" % (comm_id, header.get('msg_id',None)))

            # Message will get sent to kernel. Here we also ensure we have a registration for future use and pull out the initial data info

            h2 = {}
            for k in ['username','session','version',]:
                h2[k] = header[k]
            h2['msg_type'] = 'comm_msg'
            h2['msg_id'] = str(uuid.uuid4()).replace('-','')
            channel = 'shell'
            m2 = {'header':h2,
                  'metadata':{},
                  'channel':channel,
                  'parent_header':{},
                  'buffers':[],
                  'content':{'comm_id':comm_id,
                             'data':{'some':'junky stuff'}}}

            stream = self.channels[channel]
            session = self.session

    com = current_on_message(self, msg)

    if m2:
        session.send(stream, m2)

    return com

def wrapped_on_reply(self, stream, msg_list):
    channel = getattr(stream,'channel',None)
    msg_type = ""
    idents, fed_msg_list = self.session.feed_identities(msg_list)
    #msg = self.session.deserialize(fed_msg_list)
    #msg_type = msg['header']['msg_type']
    print("In wrapped on reply, channel is [%s] and type [%s]" % (channel, msg_type))
    print(idents)
    print(fed_msg_list)
    return current_on_reply(self, stream, msg_list)

ZMQChannelsHandler.get = wrapped_get
ZMQChannelsHandler.on_message = wrapped_on_message
ZMQChannelsHandler._on_zmq_reply = wrapped_on_reply

class RequestRedirectionHandler(IPythonHandler):

    kernel_manager = Instance('notebook.services.kernels.kernelmanager.MappingKernelManager')

    registered_apps = {}
    registered_comms = {}

    @staticmethod
    def register_comm(da_id, session, stream, base_header, comm_id):
        pass

    def send_comm(self, da_id):
        pass

    @gen.coroutine
    def get(self, da_id=None, stem=None):
        args = {k:self.get_argument(k) for k in self.request.arguments}
        self.send_with_pause(da_id, stem, args, "GET")

    @gen.coroutine
    def post(self, da_id=None, stem=None):
        args = {k:self.get_argument(k) for k in self.request.arguments}
        self.send_with_pause(da_id, stem, args, "POST")

    def check_xsrf_cookie(self):
        # Override for this handler; post permitted as the alternatives with xsrf are too awkward to contemplate
        return

    @gen.coroutine
    def send_with_pause(self, da_id, stem, args, src_type):

        reg_app = RequestRedirectionHandler.registered_apps.get(da_id, {})
        print("Sending %s to %s" % (reg_app, da_id))

        # Construct and send a session message as a Comm
        # and add a future to the list of those waiting for a response from the kernel
        # yield the future to get the response

        # need a 'yield X or wait n seconds' combo future
        # and also a 'get X or wait n seconds and try again' future for extracting registered instances

        resp = yield gen.maybe_future("RequestRedirectionHandler [%s] [%s] args [%s] from [%s]" % (da_id, stem, args, src_type))

        self.finish(resp)

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
        self.finish(RequestRedirectionHandler.register_instance(da_id, args))

def load_jupyter_server_extension(nb_app):

    web_app = nb_app.web_app

    host_pattern = '.*$'
    root_endpoint = "/app/"

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
